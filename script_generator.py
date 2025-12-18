# script_generator.py
# 이 파일은 AI를 활용하여 릴스 시나리오를 생성하는 모듈입니다.

import json
import math # 반올림을 위해 math 모듈 추가

def generate_reel_script(app_name="내우약", themes=None):
    """
    '내우약' 앱의 홍보용 인스타그램 릴스 스크립트를 생성하는 함수.
    LLM (Large Language Model)을 통해 동적으로 시나리오를 생성하는 부분을 모의합니다.

    Args:
        app_name (str): 앱의 이름.
        themes (list): 시나리오를 생성할 주제 리스트.
                       (예: ["유효기한 관리", "영양제 알림"])

    Returns:
        dict: 생성된 릴스 스크립트 데이터 (JSON 형식)
        {
            "theme": "시나리오 주제",
            "scenes": [
                {
                    "duration": 3,              # 장면 길이 (초)
                    "visual_keywords": ["keyword1", "keyword2"], # Pexels 검색 키워드
                    "narration": "장면 내 나레이션 텍스트",     # TTS로 변환될 텍스트
                    "on_screen_text": "화면에 표시될 자막/텍스트", # 영상에 오버레이될 텍스트
                    "transition": "cut"         # 장면 전환 효과 (cut, fade 등)
                },
                ...
            ]
        }
    """
    if themes is None:
        themes = ["유효기한 관리", "영양제 알림"]

    scenarios = {
        "유효기한 관리": {
            "theme": "유효기한 지난 약품 문제점 및 '내우약' 해결책",
            "scenes": [
                {
                    "duration": 3, # 초
                    "visual_keywords": ["expired medicine", "confused person", "old pills", "medicine cabinet messy"],
                    "narration": "유효기한 지난 감기약, 실수로 먹을 뻔한 적 있나요?",
                    "on_screen_text": "유효기한 지난 약품, 위험해요!",
                    "transition": "cut"
                },
                {
                    "duration": 5,
                    "visual_keywords": ["smartphone app", "scanning medicine barcode", "organized medicine shelf", "medicine alert"],
                    "narration": f"이제 {app_name} 앱으로 우리집 상비약 유효기한을 스마트하게 관리하세요!",
                    "on_screen_text": f"{app_name}: 상비약 유효기한 자동 관리",
                    "transition": "fade"
                },
                {
                    "duration": 4,
                    "visual_keywords": ["happy family", "healthy lifestyle", "safe medicine"],
                    "narration": "안전하고 건강한 우리 집! '내우약'이 똑똑하게 지켜드립니다.",
                    "on_screen_text": "안심하고 건강하게!",
                    "transition": "cut"
                },
                {
                    "duration": 3,
                    "visual_keywords": ["app store icon", "download button", "smartphone hand"],
                    "narration": "지금 바로 앱스토어에서 '내우약'을 검색해보세요!",
                    "on_screen_text": "지금 다운로드!",
                    "transition": "cut"
                }
            ]
        },
        "영양제 알림": {
            "theme": "영양제 복용 알림의 중요성 및 '내우약' 해결책",
            "scenes": [
                {
                    "duration": 4,
                    "visual_keywords": ["forgotten pills", "busy person", "calendar reminder", "pill organizer"],
                    "narration": "매일 챙겨야 할 영양제, 오늘도 깜빡하셨나요?",
                    "on_screen_text": "영양제 복용, 잊지 마세요!",
                    "transition": "cut"
                },
                {
                    "duration": 5,
                    "visual_keywords": ["smartphone notification", "taking pills", "healthy glow", "daily routine"],
                    "narration": f"{app_name} 앱이 잊지 않고 정확한 시간에 영양제 복용 알림을 보내드립니다!",
                    "on_screen_text": f"{app_name}: 맞춤 영양제 알림",
                    "transition": "fade"
                },
                {
                    "duration": 3,
                    "visual_keywords": ["energetic person", "happy morning", "sunrise", "active lifestyle"],
                    "narration": "규칙적인 영양제 복용으로 활기찬 하루를 시작하세요!",
                    "on_screen_text": "활기찬 매일!",
                    "transition": "cut"
                },
                {
                    "duration": 3,
                    "visual_keywords": ["app store icon", "search bar", "app download"],
                    "narration": "건강한 습관, '내우약'과 함께 시작하세요!",
                    "on_screen_text": "앱스토어에서 '내우약' 검색!",
                    "transition": "cut"
                }
            ]
        }
    }

    if themes and themes[0] in scenarios:
        chosen_scenario = scenarios[themes[0]]
    else:
        chosen_scenario = scenarios["유효기한 관리"] # 기본 시나리오

    # Task 1.4: 하드코딩된 시나리오의 총 길이를 계산하고, 15초에 맞게 각 장면의 길이를 비례적으로 조절하는 로직 구현.
    TARGET_DURATION = 15
    current_total_duration = sum(scene['duration'] for scene in chosen_scenario['scenes'])

    if current_total_duration != TARGET_DURATION:
        if current_total_duration == 0: # 씬이 없는 경우 방지
            return chosen_scenario

        ratio = TARGET_DURATION / current_total_duration
        new_scenes = []
        # 각 씬의 길이를 비례적으로 조절
        for scene in chosen_scenario['scenes']:
            new_duration = math.ceil(scene['duration'] * ratio) # 올림하여 최소 1초 보장
            new_scenes.append({**scene, "duration": new_duration})
        
        # 조정 후 실제 총 시간 계산
        adjusted_total_duration = sum(scene['duration'] for scene in new_scenes)
        
        # 미세 조정: 올림으로 인해 발생한 오차를 첫 번째 씬에 더하거나 빼서 15초를 맞춤
        diff = TARGET_DURATION - adjusted_total_duration
        if new_scenes and diff != 0:
            new_scenes[0]['duration'] += diff
            # 최소 1초는 유지하도록
            if new_scenes[0]['duration'] < 1:
                new_scenes[0]['duration'] = 1

        chosen_scenario['scenes'] = new_scenes


    return chosen_scenario

if __name__ == "__main__":
    # 예시 스크립트 생성 및 출력 (유효기한 관리)
    print("--- 유효기한 관리 시나리오 ---")
    script_expiry = generate_reel_script(themes=["유효기한 관리"])
    print(f"총 길이: {sum(scene['duration'] for scene in script_expiry['scenes'])}초")
    print(json.dumps(script_expiry, indent=4, ensure_ascii=False))

    # 예시 스크립트 생성 및 출력 (영양제 알림)
    print("\n--- 영양제 알림 시나리오 ---")
    script_nutrition = generate_reel_script(themes=["영양제 알림"])
    print(f"총 길이: {sum(scene['duration'] for scene in script_nutrition['scenes'])}초")
    print(json.dumps(script_nutrition, indent=4, ensure_ascii=False))
