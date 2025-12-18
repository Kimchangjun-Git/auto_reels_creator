# tts_generator.py
# 이 파일은 텍스트를 음성으로 변환(TTS)하는 모듈입니다.
# gTTS (Google Translate) -> edge-tts (Microsoft Edge Neural Voice, Free & High Quality)로 변경됨.

from typing import Optional
import os
import edge_tts
import asyncio
import config

import json
import whisper
import torch

def extract_timing_with_whisper(audio_path: str) -> list:
    """
    Whisper를 사용하여 오디오 파일에서 단어별 타이밍을 추출합니다.
    
    Args:
        audio_path: MP3 오디오 파일 경로
        
    Returns:
        List[dict]: [{"word": "안녕", "start": 0.0, "end": 0.5, "duration": 0.5}, ...]
    """
    try:
        print("    Whisper로 타이밍 데이터 추출 중...")
        
        # Whisper 모델 로드 (base 모델 사용, 빠르고 정확도 충분)
        # 최초 1회만 다운로드됨 (~140MB)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisper.load_model("base", device=device)
        
        # 음성 인식 (word_timestamps=True로 단어별 타이밍 활성화)
        result = model.transcribe(
            audio_path,
            language="ko",  # 한국어 지정
            word_timestamps=True,
            verbose=False
        )
        
        # 타이밍 데이터 추출
        word_timings = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                word_timings.append({
                    "word": word_info["word"].strip(),
                    "start": word_info["start"],
                    "end": word_info["end"],
                    "duration": word_info["end"] - word_info["start"]
                })
        
        return word_timings
        
    except Exception as e:
        print(f"    Warning: Whisper 타이밍 추출 실패: {e}")
        return []

async def _generate_audio_async(text: str, filename: str, voice: str, rate: str) -> None:
    """
    edge-tts를 사용하여 오디오 파일과 타이밍 정보(JSON)를 생성합니다.
    """
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    
    # 2. 스트림 처리 및 메타데이터 수집
    audio_data = bytearray()
    word_timings = [] # List of {word, start, end}
    
    # WordBoundary 이벤트는 없을 수도 있음 (언어/보이스에 따라 다름).
    # 없을 경우 문장 단위라도 최대한 매칭.
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            # WordBoundary: {'offset': 1230000, 'duration': 500000, 'text': 'Hello'} (nano-seconds/100ns units usually)
            # Edge-TTS offset/duration is in 100ns units (0.1 microseconds).
            # Convert to seconds: value / 10,000,000
            start_sec = chunk["offset"] / 10_000_000
            end_sec = (chunk["offset"] + chunk["duration"]) / 10_000_000
            word_timings.append({
                "word": chunk["text"],
                "start": start_sec,
                "end": end_sec,
                "duration": end_sec - start_sec
            })

    # 오디오 파일 저장
    with open(filename, "wb") as f:
        f.write(audio_data)

    # 타이밍 정보 저장 (.json)
    if word_timings:
        json_filename = filename.replace(".mp3", ".json")
        with open(json_filename, "w", encoding='utf-8') as f:
            json.dump(word_timings, f, ensure_ascii=False, indent=2)
            print(f"타이밍 정보 저장 완료: {json_filename}")
    else:
        print("Info: WordBoundary 이벤트가 반환되지 않았습니다. (타이밍 정보 없음)")

def create_narration(text: str, output_path: str) -> Optional[str]:
    """
    텍스트를 입력받아 MP3 파일로 저장하고 경로를 반환합니다.
    (gTTS 대신 고품질 edge-tts 사용)
    """
    try:
        # 출력 디렉토리가 없으면 생성
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 비동기 함수를 동기적으로 실행
        # config.TTS_VOICE가 없으면 기본값 사용 (한국어의 경우 WordBoundary 지원 여부 확인 필요)
        # ko-KR-SunHiNeural은 지원한다고 알려져 있음.
        voice = getattr(config, 'TTS_VOICE', "ko-KR-SunHiNeural")
        rate = getattr(config, 'TTS_RATE', "+0%")
        
        asyncio.run(_generate_audio_async(text, output_path, voice, rate))
        print(f"나레이션 생성 완료 (edge-tts): {output_path}")
        
        # Whisper로 타이밍 추출 (새로 추가)
        word_timings = extract_timing_with_whisper(output_path)
        
        if word_timings:
            # JSON 파일로 저장
            json_filename = output_path.replace(".mp3", ".json")
            with open(json_filename, "w", encoding='utf-8') as f:
                json.dump(word_timings, f, ensure_ascii=False, indent=2)
            print(f"    ✅ Whisper 타이밍 정보 저장 완료: {json_filename} ({len(word_timings)}개 단어)")
        else:
            print("    ⚠️ Whisper 타이밍 추출 실패, 기존 방식(글자수 비례) 사용")
        
        return output_path
    
    except Exception as e:
        print(f"Error creating narration with edge-tts: {e}")
        return None

if __name__ == "__main__":
    # 테스트를 위한 임시 출력 디렉토리 생성
    test_output_dir = "temp_narration_audio"
    os.makedirs(test_output_dir, exist_ok=True)

    # 테스트 나레이션 생성
    text1 = "안녕하세요. 내우약 앱입니다. 목소리가 훨씬 자연스러워졌나요?"
    filepath1 = os.path.join(test_output_dir, "test_edge_tts.mp3")
    
    # config가 없을 경우를 대비한 Mock
    if not hasattr(config, 'TTS_VOICE'):
        config.TTS_VOICE = "ko-KR-SunHiNeural"

    created_file1 = create_narration(text1, filepath1)
    if created_file1:
        print(f"테스트 나레이션 저장 위치: {created_file1}")
    else:
        print("테스트 나레이션 생성 실패.")