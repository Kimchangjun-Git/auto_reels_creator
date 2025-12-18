from PIL import Image, ImageTk
# Pillow 10 compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import os
import json
import traceback
import time
from moviepy.editor import VideoFileClip
from tkVideoPlayer import TkinterVideo
import av

# tkVideoPlayer compatibility fix for newer 'av' library
_original_av_open = av.open

class ContainerWrapper:
    def __init__(self, container):
        self.container = container
    def __getattr__(self, name):
        return getattr(self.container, name)
    def __setattr__(self, name, value):
        if name in ("container", "fast_seek", "discard_corrupt"):
            self.__dict__[name] = value
        else:
            setattr(self.container, name, value)
    def __enter__(self):
        self.container.__enter__()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.container.__exit__(exc_type, exc_val, exc_tb)

def patched_av_open(*args, **kwargs):
    container = _original_av_open(*args, **kwargs)
    return ContainerWrapper(container)

av.open = patched_av_open

# 3. tkVideoPlayer AttributeError: 'NoneType' object has no attribute 'close' fix
# 이 라이브러리는 컨테이너가 None일 때도 close()를 호출하는 버그가 있어 이를 패치합니다.
original_tk_load = TkinterVideo._load

def safe_tk_load(self, *args, **kwargs):
    if self._container is None:
        class DummyContainer:
            def close(self): pass
        self._container = DummyContainer()
    try:
        if hasattr(self, "_path"):
            # print(f"  [Player Patch] Loading: {self._path}") 
            pass
        return original_tk_load(self, *args, **kwargs)
    except Exception as e:
        msg = str(e)
        path = getattr(self, "_path", "Unknown")
        print(f"  [Player Patch] _load failed for {path}: {msg}")

TkinterVideo._load = safe_tk_load

# 백엔드 로직 임포트
from main import generate_script_pipeline, generate_video_pipeline
import config
from ai_script_generator import check_api_health


class ReelsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎬 Auto Reels Creator")
        self.geometry("1100x850") # 플레이어 공간을 위해 조금 더 넓게 설정
        
        # 스타일 설정
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.configure_styles()

        # 데이터 통신용 큐
        self.progress_queue = queue.Queue()

        # 메인 컨테이너
        self.main_container = ttk.Frame(self, padding="15")
        self.main_container.pack(expand=True, fill=tk.BOTH)

        # 왼쪽 패널 (기존 입력 창)
        self.left_panel = ttk.Frame(self.main_container)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 20))

        # 오른쪽 패널 (미리보기 전용)
        self.right_panel = ttk.Frame(self.main_container, relief=tk.RIDGE, padding=10)
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 오른쪽 패널 제목
        ttk.Label(self.right_panel, text="릴스 미리보기", style='Header.TLabel').pack(pady=5)

        # 비디오 플레이어 프레임 (9:16 비율 고정: 360x640)
        self.player_container = ttk.Frame(self.right_panel, width=360, height=640)
        self.player_container.pack_propagate(False) # 크기 고정
        self.player_container.pack(pady=10)

        # 비디오 플레이어 위젯
        self.video_player = TkinterVideo(master=self.player_container, scaled=True)
        self.video_player.pack(expand=True, fill="both")
        
        # 썸네일/플레이용 라벨 (비디오 로드 전 표시)
        self.thumbnail_label = ttk.Label(self.player_container)
        self.thumbnail_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # 오른쪽 패널 버튼 프레임
        self.preview_buttons = ttk.Frame(self.right_panel)
        self.preview_buttons.pack(pady=10, fill=tk.X)

        self.play_button = ttk.Button(self.preview_buttons, text="▶️ 영상 재생", command=self.toggle_playback, state=tk.DISABLED, style='Primary.TButton')
        self.play_button.pack(side=tk.LEFT, padx=5)


        self.external_play_button = ttk.Button(self.preview_buttons, text="🎬 외부 플레이어 재생 (소리 포함)", command=self.play_externally, state=tk.DISABLED, style='Primary.TButton')
        self.external_play_button.pack(side=tk.LEFT, padx=5)

        # 재생 상태
        self.is_playing = False
        self.current_video_path = None
        self.current_script_data = None # 현재 생성된 스크립트 데이터 저장

        # UI 위젯 생성 (왼쪽 패널에 배치)
        self.create_widgets()

        # 큐 폴링 시작
        self.after(100, self.process_queue)
        
        # API 상태 확인 시작
        self.check_api_status()

    def configure_styles(self):
        """UI 스타일을 설정합니다."""
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Pretendard', 11))
        self.style.configure('Header.TLabel', font=('Pretendard', 18, 'bold'), foreground='#333')
        self.style.configure('TButton', font=('Pretendard', 12, 'bold'), padding=10)
        self.style.configure('Primary.TButton', background='#007AFF', foreground='white')
        self.style.map('Primary.TButton',
            background=[('active', '#0056b3')],
        )
        self.style.configure('TEntry', font=('Pretendard', 11), padding=5)
        self.style.configure('TCombobox', font=('Pretendard', 11), padding=5)
        self.style.configure('TProgressbar', thickness=15)
        # 상태 라벨 스타일
        self.style.configure('Status.Ok.TLabel', foreground='green', background='#f0f0f0', font=('Pretendard', 10))
        self.style.configure('Status.Error.TLabel', foreground='red', background='#f0f0f0', font=('Pretendard', 10))
        self.style.configure('Status.Checking.TLabel', foreground='orange', background='#f0f0f0', font=('Pretendard', 10))

    def create_widgets(self):
        # 헤더 라벨
        header_label = ttk.Label(self.left_panel, text="릴스 생성기", style='Header.TLabel')
        header_label.pack(pady=10)

        # --- 단계 1: 대본 생성 설정 ---
        step1_frame = ttk.LabelFrame(self.left_panel, text=" 1. 대본 자동 생성 설정 ", padding=10)
        step1_frame.pack(pady=5, fill=tk.X)

        ttk.Label(step1_frame, text="릴스 주제:").pack(anchor=tk.W)
        self.theme_entry = ttk.Entry(step1_frame, width=45)
        self.theme_entry.pack(pady=5)
        self.theme_entry.insert(0, "재미있는 건강 상식")

        ttk.Label(step1_frame, text="영상 길이 (초):").pack(anchor=tk.W)
        self.duration_entry = ttk.Entry(step1_frame, width=45)
        self.duration_entry.pack(pady=5)
        self.duration_entry.insert(0, "15")

        ttk.Label(step1_frame, text="AI 엔진:").pack(anchor=tk.W)
        self.provider_var = tk.StringVar(value="groq")
        provider_combo = ttk.Combobox(step1_frame, textvariable=self.provider_var, values=["gemini", "groq"], state="readonly", width=42)
        provider_combo.pack(pady=5)

        self.generate_script_button = ttk.Button(step1_frame, text="📝 1단계: 스크립트 생성", command=self.generate_script)
        self.generate_script_button.pack(pady=10)

        # --- 단계 2: 대본 검토 및 수정 ---
        step2_frame = ttk.LabelFrame(self.left_panel, text=" 2. 대본 검토 및 수정 ", padding=10)
        step2_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.script_text = tk.Text(step2_frame, height=10, width=45, font=('Pretendard', 10))
        self.script_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        script_scroll = ttk.Scrollbar(step2_frame, command=self.script_text.yview)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.script_text.config(yscrollcommand=script_scroll.set)
        self.script_text.insert(tk.END, "// 생성된 스크립트가 여기에 표시됩니다.")

        # --- 단계 3: 영상 제작 ---
        step3_frame = ttk.LabelFrame(self.left_panel, text=" 3. 최종 영상 제작 ", padding=10)
        step3_frame.pack(pady=5, fill=tk.X)

        self.generate_video_button = ttk.Button(step3_frame, text="🎬 2단계: 영상 제작 시작", command=self.start_video_generation, state=tk.DISABLED, style='Primary.TButton')
        self.generate_video_button.pack(pady=10)

        # API 상태 (작게 표시)
        api_status_frame = ttk.Frame(self.left_panel)
        api_status_frame.pack(pady=5, fill=tk.X)
        
        ttk.Label(api_status_frame, text="Gemini:", font=('Pretendard', 9)).pack(side=tk.LEFT)
        self.gemini_status_var = tk.StringVar(value="Checking...")
        ttk.Label(api_status_frame, textvariable=self.gemini_status_var, style='Status.Checking.TLabel', font=('Pretendard', 9)).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(api_status_frame, text="Groq:", font=('Pretendard', 9)).pack(side=tk.LEFT)
        self.groq_status_var = tk.StringVar(value="Checking...")
        ttk.Label(api_status_frame, textvariable=self.groq_status_var, style='Status.Checking.TLabel', font=('Pretendard', 9)).pack(side=tk.LEFT)

        # 프로그레스 바 & 상태
        self.progress_bar = ttk.Progressbar(self.left_panel, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=10)

        self.status_var = tk.StringVar(value="준비 완료")
        status_label = ttk.Label(self.left_panel, textvariable=self.status_var, wraplength=400)
        status_label.pack(pady=5)

        # 미리보기 안내 문구 (오른쪽 패널 하단)
        self.preview_notice = ttk.Label(self.right_panel, text="⚠️ 미리보기 창에서는 소리가 나지 않습니다. \n소리 확인은 '외부 플레이어 재생' 버튼을 눌러주세요.", 
                                        font=('Pretendard', 10, 'italic'), foreground='#666', justify=tk.CENTER)
        self.preview_notice.pack(pady=5)

    def check_api_status(self):
        """API 상태를 확인합니다."""
        def check():
            for provider in ["gemini", "groq"]:
                is_healthy, msg = check_api_health(provider)
                self.progress_queue.put(("api_status", {"provider": provider, "message": msg, "is_ok": is_healthy}))

        threading.Thread(target=check, daemon=True).start()

    def generate_script(self):
        """1단계: 스크립트 생성을 시작합니다."""
        theme = self.theme_entry.get().strip()
        duration_str = self.duration_entry.get().strip()
        provider = self.provider_var.get()

        if not theme:
            messagebox.showerror("입력 오류", "주제를 입력해주세요.")
            return

        try:
            duration = int(duration_str) if duration_str else 30
        except ValueError:
            messagebox.showerror("입력 오류", "영상 길이는 숫자여야 합니다.")
            return

        self.generate_script_button.config(state=tk.DISABLED, text="📝 스크립트 생성 중...")
        self.generate_video_button.config(state=tk.DISABLED)
        self.progress_bar["value"] = 5
        self.status_var.set("AI 작가가 스크립트를 작성 중입니다...")
        
        def run():
            try:
                def progress_callback(percent, message):
                    self.progress_queue.put(("progress", (percent, message)))

                script_data = generate_script_pipeline("내우약", theme, duration, provider, progress_callback)
                if script_data:
                    self.progress_queue.put(("script_ready", script_data))
                else:
                    raise Exception("스크립트 생성 결과가 없습니다.")
            except Exception as e:
                self.progress_queue.put(("error", str(e)))

        threading.Thread(target=run, daemon=True).start()

    def start_video_generation(self):
        """2단계: 영상 제작을 시작합니다."""
        # 텍스트 박스에서 수정된 스크립트 읽기
        edited_script_str = self.script_text.get(1.0, tk.END).strip()
        try:
            self.current_script_data = json.loads(edited_script_str)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON 오류", f"스크립트 형식이 올바르지 않습니다. JSON 형식을 유지해주세요.\n{e}")
            return

        duration_str = self.duration_entry.get().strip()
        try:
            duration = int(duration_str) if duration_str else 30
        except ValueError:
            duration = 30

        self.generate_video_button.config(state=tk.DISABLED, text="📹 영상 제작 중...")
        self.generate_script_button.config(state=tk.DISABLED)
        self.status_var.set("영상 제작을 시작합니다...")
        
        # 이전 재생 중지
        self.stop_playback()
        self.thumbnail_label.config(image="")
        self.thumbnail_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.play_button.config(state=tk.DISABLED, text="▶️ 영상 재생")
        self.current_video_path = None

        def run():
            try:
                def progress_callback(percent, message):
                    self.progress_queue.put(("progress", (percent, message)))

                final_path = generate_video_pipeline(self.current_script_data, target_duration=duration, progress_callback=progress_callback)
                if final_path:
                    self.progress_queue.put(("complete", final_path))
                else:
                    raise Exception("영상 제작 실패")
            except Exception as e:
                self.progress_queue.put(("error", str(e)))

        threading.Thread(target=run, daemon=True).start()

    def process_queue(self):
        """백그라운드 스레드의 메시지를 처리합니다."""
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                if msg_type == "progress":
                    percent, message = data
                    self.progress_bar["value"] = percent
                    self.status_var.set(message)
                elif msg_type == "script_ready":
                    self.current_script_data = data
                    self.script_text.delete(1.0, tk.END)
                    self.script_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
                    self.generate_script_button.config(state=tk.NORMAL, text="📝 스크립트 재생성")
                    self.generate_video_button.config(state=tk.NORMAL)
                    self.status_var.set("스크립트 생성 완료! 내용을 검토하고 '영상 제작 시작'을 눌러주세요.")
                elif msg_type == "complete":
                    self.current_video_path = data
                    self.generate_video_button.config(state=tk.NORMAL, text="🎬 2단계: 영상 제작 시작")
                    self.generate_script_button.config(state=tk.NORMAL)
                    self.play_button.config(state=tk.NORMAL)
                    self.external_play_button.config(state=tk.NORMAL)
                    self.status_var.set("모든 작업 완료!")
                    
                    # 비디오 파일 존재 확인 및 로드 (상대 경로 사용 - 라이브러리 호환성)
                    import time
                    time.sleep(0.5) # 파일 쓰기 완료 후 OS 안정화 대기
                    
                    abs_path = os.path.abspath(data)
                    rel_path = os.path.relpath(abs_path, os.getcwd())
                    
                    if os.path.exists(abs_path):
                        print(f"  [Player] Loading video: {rel_path}")
                        self.video_player.load(rel_path)
                        self.generate_thumbnail(abs_path)
                        
                        if messagebox.askyesno("성공", "릴스 영상이 성공적으로 제작되었습니다. 지금 재생할까요?"):
                            self.start_playback()
                    else:
                        print(f"  ❌ 오류: 생성된 파일이 경로에 없습니다: {data}")
                        messagebox.showerror("오류", f"영상을 찾을 수 없습니다: {data}")
                elif msg_type == "api_status":
                    p = data["provider"]
                    msg = data["message"]
                    var = self.gemini_status_var if p == "gemini" else self.groq_status_var
                    var.set(msg)
                elif msg_type == "error":
                    messagebox.showerror("오류 발생", data)
                    self.status_var.set(f"오류: {data}")
                    self.generate_script_button.config(state=tk.NORMAL, text="📝 1단계: 스크립트 생성")
                    self.generate_video_button.config(state=tk.DISABLED, text="🎬 2단계: 영상 제작 시작")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)
            
    def generate_thumbnail(self, video_path):
        """영상 썸네일 생성 및 표시"""
        try:
            clip = VideoFileClip(video_path)
            frame = clip.get_frame(0)
            clip.close()
            
            img = Image.fromarray(frame)
            # 플레이어 크기에 맞게 리사이즈 (9:16)
            img.thumbnail((360, 640))
            
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_label.config(image=photo)
            self.thumbnail_label.image = photo
            self.thumbnail_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.thumbnail_label.lift()
        except Exception as e:
            print(f"썸네일 생성 실패: {e}")

    def toggle_playback(self):
        """재생/일시정지 토글"""
        if not self.current_video_path: return
        
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """재생 시작"""
        self.thumbnail_label.place_forget() # 썸네일 숨기기
        self.video_player.play()
        self.is_playing = True
        self.play_button.config(text="⏸️ 일시 정지")
        
        # 영상이 끝나면 자동으로 상태를 변경하기 위한 루프 (tkVideoPlayer는 완료 이벤트를 기본적으로 제공하지 않을 수 있음)
        self.check_playback()

    def stop_playback(self):
        """일시 정지 및 중지"""
        try:
            self.video_player.stop()
        except:
            self.video_player.pause()
        self.is_playing = False
        self.play_button.config(text="▶️ 영상 재생")

    def check_playback(self):
        """재생 상태 확인"""
        if self.is_playing:
            # tkvideoplayer의 내부 상태를 확인하거나 타이머로 관리 가능
            pass
        # 실제로는 사용자가 일시정지 버튼을 누를 때까지 재생 상태 유지

    def open_file_location(self, path):
        """폴더 열기"""
        if not path: return
        try:
            target = os.path.dirname(path)
            if os.name == 'nt':
                os.startfile(target)
            elif os.uname().sysname == 'Darwin':
                os.system(f'open "{target}"')
            else:
                os.system(f'xdg-open "{target}"')
        except Exception as e:
            messagebox.showerror("오류", f"폴더를 열 수 없습니다: {e}")

    def play_externally(self):
        """외부 플레이어로 재생"""
        if not self.current_video_path: return
        try:
            abs_path = os.path.abspath(self.current_video_path)
            if os.name == 'nt':
                os.startfile(abs_path)
            elif os.uname().sysname == 'Darwin':
                import subprocess
                subprocess.run(["open", abs_path])
            else:
                os.system(f'xdg-open "{abs_path}"')
        except Exception as e:
            messagebox.showerror("오류", f"외부 플레이어를 실행할 수 없습니다: {e}")

if __name__ == "__main__":
    app = ReelsApp()
    app.mainloop()