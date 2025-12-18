# video_assembler.py
# 이 파일은 다운로드된 미디어와 생성된 나레이션, 텍스트를 조합하여 최종 릴스 영상을 편집하는 모듈입니다.

from PIL import Image, ImageDraw, ImageFont
# Pillow 10 compatibility for MoviePy
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import VideoFileClip, ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip, vfx, afx
import os
import math
import random
import glob
import uuid # For unique filenames
import numpy as np
import sys
import traceback
import moviepy

import config
from typing import List, Optional
from sfx_downloader import download_sfx

# 릴스 표준 해상도 (9:16 비율) - config에서 로드
REELS_ASPECT_RATIO = config.REELS_WIDTH / config.REELS_HEIGHT

def create_ken_burns_clip(image_path: str, duration: float, target_resolution: tuple,
                           start_zoom: float = 1.0, end_zoom: float = 1.2,
                           start_x_rel: float = 0.5, start_y_rel: float = 0.5, # relative center position 0 to 1
                           end_x_rel: float = 0.5, end_y_rel: float = 0.5) -> ImageClip:
    """
    Creates a Ken Burns effect clip from an image by smoothly zooming and panning.

    This optimized version calculates a viewport to crop from the original image
    and then resizes the cropped portion to the target resolution, which is
    generally more efficient than resizing the entire image and then positioning.

    Args:
        image_path (str): Path to the input image file.
        duration (float): Duration of the output clip in seconds.
        target_resolution (tuple): Desired (width, height) of the output clip.
        start_zoom (float): Initial zoom level (e.g., 1.0 for original size, 2.0 for 2x zoom).
                            A value > 1.0 means the source image viewport is smaller.
        end_zoom (float): Final zoom level.
        start_x_rel (float): Relative X-coordinate (0.0 to 1.0) of the viewport center at the start.
        start_y_rel (float): Relative Y-coordinate (0.0 to 1.0) of the viewport center at the start.
        end_x_rel (float): Relative X-coordinate (0.0 to 1.0) of the viewport center at the end.
        end_y_rel (float): Relative Y-coordinate (0.0 to 1.0) of the viewport center at the end.
    
    Returns:
        ImageClip: The resulting clip with the Ken Burns effect applied.
    """
    # Load the image once using PIL for efficiency
    img = Image.open(image_path)
    img_width, img_height = img.size

    # Calculate initial and final viewport sizes based on zoom levels
    # Viewport size = original size / zoom (larger zoom means smaller viewport = zoomed in)
    start_viewport_width = img_width / start_zoom
    start_viewport_height = img_height / start_zoom
    end_viewport_width = img_width / end_zoom
    end_viewport_height = img_height / end_zoom

    # Ensure viewport maintains aspect ratio of target resolution
    target_width, target_height = target_resolution
    target_aspect = target_width / target_height

    # Adjust viewport heights to match target aspect ratio (assuming width is limiting)
    start_viewport_height = start_viewport_width / target_aspect
    end_viewport_height = end_viewport_width / target_aspect

    # Ensure viewport doesn't exceed image bounds
    if start_viewport_height > img_height:
        start_viewport_height = img_height
        start_viewport_width = start_viewport_height * target_aspect
    if end_viewport_height > img_height:
        end_viewport_height = img_height
        end_viewport_width = end_viewport_height * target_aspect

    # Calculate start and end viewport positions (top-left coordinates)
    start_center_x = img_width * start_x_rel
    start_center_y = img_height * start_y_rel
    end_center_x = img_width * end_x_rel
    end_center_y = img_height * end_y_rel

    start_left = max(0, start_center_x - start_viewport_width / 2)
    start_top = max(0, start_center_y - start_viewport_height / 2)
    end_left = max(0, end_center_x - end_viewport_width / 2)
    end_top = max(0, end_center_y - end_viewport_height / 2)

    # Ensure viewport doesn't go beyond right/bottom edges
    if start_left + start_viewport_width > img_width:
        start_left = img_width - start_viewport_width
    if start_top + start_viewport_height > img_height:
        start_top = img_height - start_viewport_height
    if end_left + end_viewport_width > img_width:
        end_left = img_width - end_viewport_width
    if end_top + end_viewport_height > img_height:
        end_top = img_height - end_viewport_height

    def make_frame(t):
        # Linear interpolation for position and size
        progress = t / duration
        current_left = start_left + (end_left - start_left) * progress
        current_top = start_top + (end_top - start_top) * progress
        current_width = start_viewport_width + (end_viewport_width - start_viewport_width) * progress
        current_height = start_viewport_height + (end_viewport_height - start_viewport_height) * progress

        # Crop the viewport from the original image
        cropped_img = img.crop((current_left, current_top, current_left + current_width, current_top + current_height))

        # Resize to target resolution using LANCZOS for high quality
        resized_img = cropped_img.resize(target_resolution, Image.LANCZOS)

        # Convert to numpy array for MoviePy
        return np.array(resized_img)

    # Create the ImageClip with the make_frame function
    return ImageClip(make_frame, duration=duration)

def generate_text_overlay(text: str, font_path: str, font_size: int, color: str = "white",
                          stroke_color: str = "black", stroke_width: int = 2,
                          highlight_color: str = "yellow",
                          bg_enabled: bool = True, bg_color: tuple = (0, 0, 0, 180),
                          bg_padding: int = 40, border_radius: int = 25,
                          max_width: int = 1000, line_spacing: float = 1.3) -> str:
    """
    PIL을 사용하여 고품질 텍스트 오버레이 이미지를 생성합니다.
    - 자동 줄바꿈 지원
    - *강조* 텍스트를 인식하여 highlight_color 적용
    - 반투명 둥근 모서리 배경 박스 지원
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"Warning: Font '{font_path}' not found. Using default font.")
        font = ImageFont.load_default()

    # 1. 텍스트 줄바꿈 처리
    lines = []
    # 텍스트에서 강조 표시를 무시하고 너비를 계산하기 위해 임시로 제거
    clean_text = text.replace('*', '')
    words = text.split()
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word]).replace('*', '')
        bbox = font.getbbox(test_line)
        if (bbox[2] - bbox[0]) <= max_width - (bg_padding * 2):
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(' '.join(current_line))

    # 2. 텍스트 크기 측정 (최대 너비와 총 높이)
    line_infos = []
    max_line_width = 0
    total_text_height = 0
    
    for line in lines:
        clean_line = line.replace('*', '')
        bbox = font.getbbox(clean_line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_infos.append({'text': line, 'width': w, 'height': h})
        max_line_width = max(max_line_width, w)
    
    # 줄 사이 간격 포함 총 높이
    line_h = line_infos[0]['height'] if line_infos else font_size
    total_text_height = sum(info['height'] for info in line_infos) + (len(lines) - 1) * int(line_h * (line_spacing - 1))

    # 3. 이미지 크기 결정 (배경 패딩 포함)
    img_width = max_line_width + (bg_padding * 2)
    img_height = total_text_height + (bg_padding * 2)
    
    # 캔버스 생성 (RGBA)
    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 4. 배경 박스 그리기
    if bg_enabled:
        draw.rounded_rectangle(
            [(0, 0), (img_width, img_height)],
            radius=border_radius,
            fill=bg_color
        )

    # 5. 줄별로 텍스트 그리기
    current_y = bg_padding
    for info in line_infos:
        line_text = info['text']
        line_w = info['width']
        start_x = (img_width - line_w) / 2 # 가운데 정렬
        
        # 강조 텍스트(asterisks) 파싱 및 그리기
        parts = []
        is_highlight = False
        temp_part = ""
        
        # 간단한 유한 상태 기계로 강조 파싱
        idx = 0
        while idx < len(line_text):
            if line_text[idx] == '*':
                if temp_part:
                    parts.append((temp_part, is_highlight))
                is_highlight = not is_highlight
                temp_part = ""
            else:
                temp_part += line_text[idx]
            idx += 1
        if temp_part:
            parts.append((temp_part, is_highlight))
            
        x_cursor = start_x
        for part_text, highlight in parts:
            current_color = highlight_color if highlight else color
            # 텍스트 그리기 (스트로크 포함)
            if stroke_width > 0:
                # PIL의 text stroke 기능 사용 (있는 경우)
                if hasattr(draw, 'text'):
                    draw.text((x_cursor, current_y), part_text, font=font, fill=current_color,
                              stroke_width=stroke_width, stroke_fill=stroke_color)
                else:
                    # 구버전 방식
                    for dx in range(-stroke_width, stroke_width + 1):
                        for dy in range(-stroke_width, stroke_width + 1):
                            if dx != 0 or dy != 0:
                                draw.text((x_cursor + dx, current_y + dy), part_text, font=font, fill=stroke_color)
                    draw.text((x_cursor, current_y), part_text, font=font, fill=current_color)
            else:
                draw.text((x_cursor, current_y), part_text, font=font, fill=current_color)
            
            # 다음 파트를 위해 x_cursor 이동
            part_bbox = font.getbbox(part_text)
            x_cursor += part_bbox[2] - part_bbox[0]
            
        current_y += info['height'] * line_spacing

    # 6. 저장 및 경로 반환
    temp_dir = "temp_overlays"
    os.makedirs(temp_dir, exist_ok=True)
    overlay_path = os.path.join(temp_dir, f"overlay_{uuid.uuid4().hex}.png")
    img.save(overlay_path)
    
    return overlay_path

def apply_transition(clip: VideoFileClip, transition_type: str, duration: float = 0.5) -> VideoFileClip:
    """
    클립에 전환 효과를 적용합니다.
    """
    if transition_type == "fade":
        return clip.fx(vfx.fadein, duration)
    elif transition_type == "crossfade":
        return clip.fx(vfx.crossfadein, duration)  # 수정: 직접 crossfadein 호출 대신 fx(vfx.crossfadein) 사용
    else:
        return clip  # 기본: 컷

def assemble_reel(scenes_data: List[dict], output_filepath: str,
                  final_duration: Optional[float] = None,
                  bgm_path: Optional[str] = None) -> Optional[str]:
    """
    장면 데이터를 받아 최종 릴스 영상을 조립합니다.
    """
    processed_clips = []
    
    # 1. 길이 정규화 (사용자가 지정한 총 길이에 맞춤)
    total_scene_duration = sum(scene.get('duration', 0) for scene in scenes_data)
    if final_duration and total_scene_duration > 0:
        ratio = final_duration / total_scene_duration
        print(f"  [길이 정규화] 총 길이 {total_scene_duration:.2f}s -> {final_duration}s (비율: {ratio:.2f})")
        for scene in scenes_data:
            scene['duration'] = scene.get('duration', 0) * ratio

    # 2. 개별 클립 생성
    current_time_offset = 0.0

    for scene in scenes_data:
        media_path = scene.get('media_path')
        duration = scene.get('duration', 5)
        narration_path = scene.get('audio_path')
        on_screen_text = scene.get('on_screen_text', '')
        transition = scene.get('transition', 'cut')

        if media_path and os.path.exists(media_path):
            try:
                if media_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    clip = create_ken_burns_clip(
                        media_path, duration,
                        target_resolution=(config.REELS_WIDTH, config.REELS_HEIGHT)
                    )
                else:
                    clip = VideoFileClip(media_path).subclip(0, duration)
                    # 모든 영상을 9:16 비율로 강제 조정
                    clip = clip.resize(height=config.REELS_HEIGHT)
                    if clip.w < config.REELS_WIDTH:
                        clip = clip.resize(width=config.REELS_WIDTH)
                    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2,
                                     width=config.REELS_WIDTH, height=config.REELS_HEIGHT)
            except Exception as e:
                print(f"  ⚠️ 미디어 로딩 실패 ({media_path}): {e}")
                clip = ColorClip((config.REELS_WIDTH, config.REELS_HEIGHT), color=(0,0,0), duration=duration)
        else:
            print(f"  ⚠️ 미디어 파일 없음, 검은 화면으로 대체: {media_path}")
            clip = ColorClip((config.REELS_WIDTH, config.REELS_HEIGHT), color=(0,0,0), duration=duration)

        if narration_path and os.path.exists(narration_path):
            try:
                # 볼륨 3.0배 증폭, 샘플레이트 44100Hz 고정
                audio = AudioFileClip(narration_path).volumex(3.0).set_fps(44100)
                if audio.duration > duration:
                    audio = audio.subclip(0, duration)
                
                # [복구] 클립에 오디오 즉시 입히기 (가장 안정적인 방식)
                clip = clip.set_audio(audio)
                print(f"    [나레이션 삽입] {os.path.basename(narration_path)} ({audio.duration:.2f}s, 볼륨: 3.0x)")
            except Exception as e:
                print(f"    ⚠️ 나레이션 로드 실패: {e}")
        
        # 자막 추가
        if on_screen_text:
            try:
                overlay_path = generate_text_overlay(
                    on_screen_text,
                    font_path=getattr(config, 'FONT_PATH', "assets/fonts/NotoSansKR-Regular.ttf"),
                    font_size=config.DEFAULT_FONT_SIZE,
                    stroke_width=config.TEXT_STROKE_WIDTH,
                    color=config.TEXT_COLOR,
                    stroke_color=config.TEXT_STROKE_COLOR,
                    highlight_color=getattr(config, 'HIGHLIGHT_TEXT_COLOR', 'yellow'),
                    bg_enabled=getattr(config, 'TEXT_BG_ENABLED', True),
                    bg_color=getattr(config, 'TEXT_BG_COLOR', (0, 0, 0, 180)),
                    bg_padding=getattr(config, 'TEXT_BG_PADDING', 40),
                    border_radius=getattr(config, 'TEXT_BORDER_RADIUS', 25)
                )
                text_position = ("center", config.REELS_HEIGHT * config.TEXT_POSITION_Y_RATIO)
                text_clip = ImageClip(overlay_path).set_duration(duration).set_position(text_position)
                
                # [복구] 자막 합성 시 오디오 유실 방지
                original_audio = clip.audio
                clip = CompositeVideoClip([clip, text_clip], size=(config.REELS_WIDTH, config.REELS_HEIGHT))
                if original_audio:
                    clip = clip.set_audio(original_audio)
            except Exception as e:
                print(f"  ⚠️ 텍스트 오버레이 추가 실패: {e}")

        clip = apply_transition(clip, transition)
        # 비디오 클립 오디오는 일단 제거 (나중에 통합 합성)
        processed_clips.append(clip)
        current_time_offset += duration

    try:
        final_video = concatenate_videoclips(processed_clips, method="chain")
        print(f"  [비디오 연결 완료] 총 길이: {final_video.duration:.2f}s")
    except Exception as e:
        print(f"  ❌ 클립 연결 실패: {e}")
        return None

    # 3. 배경음악 및 SFX 합성 (최종 연결된 비디오에 믹싱)
    if bgm_path and os.path.exists(bgm_path):
        try:
            print(f"  [배경음악] {bgm_path} 로드 중...")
            bgm_clip = AudioFileClip(bgm_path).volumex(0.6).set_fps(44100).audio_loop(duration=final_video.duration).set_start(0)
            bgm_clip = bgm_clip.fx(afx.audio_fadein, 2)
            
            # 효과음(SFX) 준비
            sfx_layers = []
            try:
                whoosh_path = download_sfx("whoosh")
                if whoosh_path:
                    whoosh_clip_base = AudioFileClip(whoosh_path).set_fps(44100).volumex(0.5)
                    if whoosh_clip_base.duration > 1.5:
                        whoosh_clip_base = whoosh_clip_base.subclip(0, 1.5)
                    
                    sfx_time = 0
                    for idx, scene in enumerate(scenes_data):
                        if idx > 0:
                            sfx_layers.append(whoosh_clip_base.set_start(sfx_time - 0.2))
                        sfx_time += scene.get('duration', 0)
            except Exception as e:
                print(f"  ⚠️ 효과음 로드 실패: {e}")

            # 최종 오디오 레이어 구성
            audio_layers = []
            if final_video.audio:
                audio_layers.append(final_video.audio)
            audio_layers.append(bgm_clip)
            audio_layers.extend(sfx_layers)

            # 모든 레이어를 스테레오로 통일 및 FPS 재확인
            safe_layers = []
            for a in audio_layers:
                try:
                    a = a.set_fps(44100)
                    safe_layers.append(a.to_stereo() if hasattr(a, 'nchannels') and a.nchannels == 1 else a)
                except:
                    safe_layers.append(a)

            if safe_layers:
                final_audio = CompositeAudioClip(safe_layers).set_duration(final_video.duration)
                final_audio.fps = 44100
                final_audio = final_audio.fx(afx.audio_fadeout, 2)
                final_video = final_video.set_audio(final_audio)
                print(f"  [오디오 믹싱 완료] 최종 레이어 수: {len(safe_layers)}")
            
        except Exception as e:
            print(f"  ⚠️ 배경음악/SFX 합성 실패: {e}")
            import traceback
            traceback.print_exc()

    try:
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"  [최종 인코딩 준비] 길이: {final_video.duration:.2f}s, 오디오 존재: {final_video.audio is not None}")
        
        # ffmpeg_params로 오디오 비트레이트 강제 지정
        final_video.write_videofile(output_filepath, 
                                     codec=getattr(config, 'FFMPEG_VIDEO_CODEC', config.REELS_CODEC), 
                                     audio_codec=config.REELS_AUDIO_CODEC, 
                                     audio=True,
                                     temp_audiofile="temp-audio.m4a",
                                     remove_temp=True,
                                     fps=config.REELS_FPS,
                                     verbose=False,
                                     logger=None,
                                     ffmpeg_params=["-b:a", "192k"], # 오디오 비트레이트 상향
                                     preset="ultrafast" if not getattr(config, 'GPU_ACCELERATION', False) else None,
                                     threads=os.cpu_count())
        
        # 생성된 파일의 오디오 존재 여부 즉시 확인 (ffprobe 활용)
        import subprocess
        try:
            check_cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", output_filepath]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            if result.stdout.strip():
                print(f"  ✅ 최종 파일 오디오 스트림 확인됨: {result.stdout.strip()}")
            else:
                print("  ❌ 릴스 생성은 완료되었으나 오디오 스트림이 감지되지 않았습니다.")
        except:
            pass
            
        print(f"릴스 영상 생성 완료: {output_filepath}")
        return output_filepath
    except Exception as e:
        print(f"릴스 영상 생성 중 오류 발생: {e}")
        return None
    finally:
        pass


if __name__ == "__main__":
    print("이 파일은 `main.py`에서 호출하여 사용하는 모듈입니다.")
    print("테스트를 원하시면 `main.py`를 실행해주세요.")