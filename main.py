# main.py
# 이 파일은 전체 릴스 생성 워크플로우를 통합하고 실행하는 메인 스크립트입니다.

import os
import json
import datetime
import config
import math
from ai_script_generator import generate_script_with_ai
from script_generator import generate_reel_script # Fallback
from media_downloader import search_and_download_video
from tts_generator import create_narration
from video_assembler import assemble_reel
from moviepy.audio.io.AudioFileClip import AudioFileClip
from video_assembler import assemble_reel
from moviepy.audio.io.AudioFileClip import AudioFileClip
from bgm_downloader import download_bgm
from ai_validator import validate_media_relevance

# API 키 확인
if not config.PEXELS_API_KEY:
    print("Warning: PEXELS_API_KEY 환경 변수가 설정되지 않았습니다. Pexels 기능을 사용할 수 없습니다.")

# 필요한 디렉토리 생성
os.makedirs(config.DOWNLOADED_MEDIA_DIR, exist_ok=True)
os.makedirs(config.NARRATION_AUDIO_DIR, exist_ok=True)
os.makedirs(config.FINAL_REELS_DIR, exist_ok=True)

def generate_script_pipeline(app_name: str, theme: str, target_duration: int, provider: str = "gemini", progress_callback=None) -> dict:
    """
    1단계: 스크립트 생성 파이프라인
    """
    # Helper to safely call callback
    def update_progress(p, msg):
        if progress_callback:
            progress_callback(p, msg)
        print(f"[{p}%] {msg}")

    update_progress(0, f"스크립트 생성 시작 (주제: {theme}, AI 엔진: {provider})")
    
    # 1. 스크립트 생성 (AI 우선 시도)
    update_progress(5, "AI 작가가 릴스 스크립트를 생성 중입니다...")
    script_data = generate_script_with_ai(topic=theme, duration=target_duration, provider=provider)
    
    if script_data is None:
        update_progress(10, "AI 생성 실패 또는 API 키 미설정. 기본 스크립트를 사용합니다.")
        script_data = generate_reel_script(app_name=app_name, themes=[theme])
    else:
        update_progress(15, "AI 스크립트 생성 완료.")

    update_progress(18, "\n[생성된 스크립트 확인 중]") # Added for more granular status
    if not script_data or not script_data.get('scenes'):
        update_progress(20, "Error: 스크립트 생성에 실패했습니다.")
        return None
    update_progress(20, "스크립트 유효성 확인 완료.") # Final status for script pipeline
    
    # 메타데이터에 테마 저장 (나중에 파일명 등에 사용)
    if 'metadata' not in script_data:
        script_data['metadata'] = {}
    script_data['metadata']['theme'] = theme
    script_data['metadata']['provider'] = provider # Provider 정보 저장
    
    return script_data

def generate_video_pipeline(script_data: dict, target_duration: int = None, mood_override: str = None, progress_callback=None) -> str:
    """
    2단계: 확정된 스크립트 데이터를 받아 영상 제작
    """
    if not script_data:
        return None
    
    # 저장된 Provider 정보 가져오기 (없으면 gemini)
    provider = script_data.get('metadata', {}).get('provider', 'gemini')

    # Helper to safely call callback
    def update_progress(p, msg):
        if progress_callback:
            progress_callback(p, msg)
        print(f"[{p}%] {msg}")

    update_progress(20, f"영상 제작 프로세스 시작... (AI Engine: {provider})")
    
    # 작업 디렉토리 생성 (이미 위에서 처리되었지만, 함수 내에서 다시 확인)
    for path in [config.DOWNLOADED_MEDIA_DIR, config.NARRATION_AUDIO_DIR, config.FINAL_REELS_DIR]:
        os.makedirs(path, exist_ok=True)

    theme = script_data.get('metadata', {}).get('theme', 'Unknown')

    # 1.5. 배경음악 준비 (옵션)
    bgm_path = None
    music_mood = script_data.get('metadata', {}).get('music_mood', 'Cheerful')
    update_progress(25, f"배경음악 준비 중... ({music_mood})")

    try:
        # BGM 다운로드 및 검증 (최대 2회 시도)
        current_mood_query = music_mood
        for attempt in range(2):
            bgm_path, bgm_metadata = download_bgm(mood=current_mood_query)
            
            if not bgm_path: # 다운로드 실패
                break
                
            # 검증
            if bgm_metadata.get("source") == "existing":
                print("  ℹ️ 기존 BGM 파일 사용 (검증 생략)")
                update_progress(27, "기존 BGM 파일 사용 (AI 검증 생략)")
                break

            # AI 검증
            update_progress(28 + attempt, f"AI 검증관이 BGM을 확인 중입니다... (시도 {attempt+1})")
            is_valid, suggestion = validate_media_relevance(
                script_context=f"Theme: {theme}. Mood: {music_mood}",
                media_metadata=bgm_metadata,
                media_type="audio",
                provider=provider # Provider 전달
            )
            
            if is_valid:
                update_progress(29, "✅ BGM 승인 완료!")
                break
            else:
                update_progress(28 + attempt, f"❌ BGM 반려됨. AI 재검색 제안: {suggestion}")
                current_mood_query = suggestion 
                if os.path.exists(bgm_path):
                    os.remove(bgm_path)
                    bgm_path = None

    except Exception as e:
        print(f"BGM 다운로드 실패: {e}")

    # 2. 각 장면에 대한 미디어 및 나레이션 생성
    processed_scenes = []
    scenes = script_data.get('scenes', [])
    total_scenes = len(scenes)

    update_progress(30, "각 장면에 대한 미디어 및 나레이션 생성 중...")
    
    # 생성 프로세스를 구분하기 위한 고유 ID
    process_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    for i, scene in enumerate(scenes):
        scene_num = scene.get('scene_number', i+1)
        narr_text = scene.get('narration', '')
        visual_keywords = scene.get('visual_keywords', [])
        keyword = visual_keywords[0] if visual_keywords else "general"
        scene_duration = scene.get('duration', 5)
        
        # 진척률 계산 (30% ~ 80% 사이를 씬 개수로 분배)
        current_percent = 30 + int((i / total_scenes) * 50)
        update_progress(current_percent, f"장면 {scene_num}/{total_scenes} 처리 중: '{keyword}'")

        print(f"  장면 {scene_num} 처리 중...")
        
        # 2-1. 나레이션 먼저 생성 (길이 측정을 위해)
        narration_text = scene.get('narration')
        generated_narration_path = None
        # scene_duration = scene['duration'] # 기본값 (혹은 최소값) # This line is now handled by the new scene_duration variable

        if narration_text:
            update_progress(current_percent + 1, f"장면 {scene_num} 나레이션 생성 중...")
            narration_filename = f"narration_{process_id}_scene_{i+1}.mp3"
            narration_filepath = os.path.join(config.NARRATION_AUDIO_DIR, narration_filename)
            generated_narration_path = create_narration(narration_text, narration_filepath)
            
            if generated_narration_path:
                try:
                    # 오디오 길이 측정
                    audio_clip = AudioFileClip(generated_narration_path)
                    audio_duration = audio_clip.duration
                    audio_clip.close()
                    
                    # 씬 길이를 오디오 길이 + 여유(0.5초)로 업데이트
                    scene_duration = math.ceil(audio_duration + 0.5)
                    update_progress(current_percent + 2, f"장면 {scene_num} 길이 자동 조정 (오디오 {audio_duration:.2f}s -> {scene_duration}s)")
                except Exception as e:
                    update_progress(current_percent + 2, f"장면 {scene_num} 오디오 길이 측정 실패. 기본 길이({scene_duration}s) 사용.")
            else:
                update_progress(current_percent + 2, f"장면 {scene_num} 나레이션 생성 실패.")
        else:
            update_progress(current_percent + 1, f"장면 {scene_num}에 나레이션 텍스트가 없습니다.")

        # 2-2. 미디어 다운로드 (AI 검증 및 재시도 포함)
        downloaded_media_path = None
        current_keyword = keyword
        
        # 최후의 수단으로 사용할 파일 경로 (항상 유지)
        last_downloaded_path = None
        
        for attempt in range(3): # 최대 3회 시도
            update_progress(current_percent + 3 + attempt, f"장면 {scene_num} 미디어 검색/다운로드 중... (키워드: '{current_keyword}', 시도 {attempt+1})")
            temp_path, media_metadata = search_and_download_video(
                keyword=current_keyword,
                output_dir=config.DOWNLOADED_MEDIA_DIR,
                duration=scene_duration
            )
            
            if not temp_path:
                update_progress(current_percent + 3 + attempt, f"장면 {scene_num} '{current_keyword}' 검색 결과 없음.")
                # 검색 실패해도 이전에 다운로드된 파일이 있으면 그것 사용
                if last_downloaded_path:
                    update_progress(current_percent + 3 + attempt, f"장면 {scene_num} 이전 시도에서 다운로드된 파일을 사용합니다.")
                    downloaded_media_path = last_downloaded_path
                continue  # break 대신 continue로 다음 시도

            # 일단 다운로드 성공하면 마지막 후보로 등록 (삭제 안함)
            last_downloaded_path = temp_path
            
            # AI 검증
            update_progress(current_percent + 4 + attempt, f"장면 {scene_num} AI 검증관이 영상을 확인 중입니다... (키워드: {current_keyword}, 시도 {attempt+1})")
            context = f"Scene Script: {scene.get('narration')}. Visual Desc: {scene.get('visual_description')}"
            
            is_valid, suggestion = validate_media_relevance(
                script_context=context,
                media_metadata=media_metadata,
                media_type="video",
                provider=provider # Provider 전달
            )
            
            if is_valid:
                update_progress(current_percent + 5 + attempt, f"장면 {scene_num} ✅ 영상 승인 완료!")
                downloaded_media_path = temp_path
                break
            else:
                update_progress(current_percent + 5 + attempt, f"장면 {scene_num} ❌ 영상 반려됨. AI 재검색 제안: {suggestion}")
                current_keyword = suggestion 
                # 파일 삭제하지 않음! 마지막 후보로 유지
                
                # 마지막 시도였다면, 그냥 이 파일 쓰자 (ColorClip보다는 나으니까)
                if attempt == 2:
                    update_progress(current_percent + 5 + attempt, f"장면 {scene_num} 마지막 시도이므로 반려된 파일이라도 사용합니다.")
                    downloaded_media_path = temp_path

        # 루프가 끝났는데도 None이면 last_downloaded_path 사용 (검은화면 방지)
        if downloaded_media_path is None and last_downloaded_path:
            update_progress(current_percent + 8, f"장면 {scene_num} 📎 마지막으로 다운로드된 파일을 사용합니다: {last_downloaded_path}")
            downloaded_media_path = last_downloaded_path

        processed_scene = {
            **scene, 
            'duration': scene_duration, # 업데이트된 duration 저장
            'media_path': downloaded_media_path,
            'audio_path': generated_narration_path
        }
        processed_scenes.append(processed_scene)

    update_progress(80, "미디어 및 나레이션 생성 완료.")

    update_progress(85, "릴스 영상 조립 및 렌더링 중... (시간이 조금 걸립니다)")
    
    # 3. 영상 조립 (assemble_reel)
    # output file name setting
    topic = script_data.get('metadata', {}).get('topic', 'reels').replace(" ", "_")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"reel_{topic}_{timestamp}.mp4"
    output_filepath = os.path.join(config.FINAL_REELS_DIR, output_filename)

    final_video_path = assemble_reel(
        scenes_data=processed_scenes,
        output_filepath=output_filepath,
        final_duration=target_duration,
        bgm_path=bgm_path
    )
    
    if final_video_path:
        update_progress(100, "완료!")
        print(f"--- 릴스 생성 최종 완료: {final_video_path} ---")
        return final_video_path
    else:
        print("Error: 릴스 영상 조립에 실패했습니다.")
        return None

def generate_full_reel(app_name: str = "내우약", theme: str = "유효기한 관리", final_duration: int = 15, mood_override: str = None, progress_callback=None):
    """
    통합 실행 함수 (하위 호환성 및 한 번에 실행용)
    """
    target_duration = final_duration if final_duration else 30
    script_data = generate_script_pipeline(app_name, theme, target_duration, progress_callback=progress_callback)
    
    if not script_data:
        return None
        
    return generate_video_pipeline(script_data, target_duration, mood_override, progress_callback=progress_callback)

if __name__ == "__main__":
    if not config.PEXELS_API_KEY:
        print("환경 변수 'PEXELS_API_KEY'가 설정되어 있지 않습니다.")
        print("`export PEXELS_API_KEY='YOUR_PEXELS_API_KEY'` 명령어로 설정 후 다시 실행해주세요.")
    else:
        # 사용자 입력 받기
        print("\n" + "="*40)
        user_theme = input("생성할 릴스의 주제를 입력하세요 (엔터 시 '재미있는 건강 상식'): ").strip()
        print("="*40 + "\n")

        if not user_theme:
            THEME = "재미있는 건강 상식"
        else:
            THEME = user_theme

        # 사용자로부터 영상 길이 입력 받기
        print("\n" + "="*40)
        user_duration = input("영상의 길이를 초 단위로 입력하세요 (엔터 시 30초): ").strip()
        print("="*40 + "\n")

        if not user_duration:
            DURATION = 30
        else:
            try:
                DURATION = int(user_duration)
            except ValueError:
                print("잘못된 입력입니다. 기본값 30초로 설정합니다.")
                DURATION = 30

        # APP_NAME은 config 모듈에서 가져오거나 다른 곳에서 정의되어 있다고 가정
        # 여기서는 예시로 "내우약"을 사용합니다. 실제 사용 시에는 적절히 정의해야 합니다.
        APP_NAME = "내우약" 
        generate_full_reel(app_name=APP_NAME, theme=THEME, final_duration=DURATION)