import json
import os

SETTINGS_FILE = 'settings.json'

class SettingsManager:
    """
    애플리케이션 설정을 settings.json 파일에서 관리하는 클래스입니다.
    """
    def __init__(self):
        self.settings = self._load_settings()
        # 로드 시점에 기본값이 없으면 config의 기본값을 즉시 반영할 수 있도록 구조 변경
        # 하지만, 이 클래스는 순수하게 파일 I/O만 담당하는게 좋음
        # config.py에서 get 호출 시 기본값을 제공하는 패턴이 더 안전

    def _load_settings(self):
        """
        settings.json 파일에서 설정을 로드합니다. 파일이 없으면 빈 딕셔너리를 반환합니다.
        """
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: {SETTINGS_FILE} 파일을 읽는 중 오류가 발생했습니다. ({e}). 기본 설정으로 시작합니다.")
                return {}
        return {}

    def get(self, key, default=None):
        """
        설정 값을 가져옵니다. 키가 없으면 기본값을 반환합니다.
        """
        return self.settings.get(key, default)

    def set(self, key, value):
        """
        설정 값을 설정하고 파일에 저장합니다.
        """
        self.settings[key] = value
        self._save_settings()

    def _save_settings(self):
        """
        현재 설정을 settings.json 파일에 저장합니다.
        """
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error: {SETTINGS_FILE} 파일에 쓰는 중 오류가 발생했습니다: {e}")

# 전역적으로 사용할 수 있는 SettingsManager 인스턴스 생성
settings_manager = SettingsManager()

if __name__ == '__main__':
    # 모듈 단독 실행 시 테스트 코드
    print("--- SettingsManager 테스트 ---")
    
    # 1. 초기값 가져오기 (파일이 없거나 비어있을 때)
    print(f"초기 PEXELS_API_KEY: {settings_manager.get('PEXELS_API_KEY', 'default_pexels_key')}")

    # 2. 새로운 값 설정 및 저장
    print("\n'NEW_PEXELS_KEY'로 값 설정...")
    settings_manager.set('PEXELS_API_KEY', 'NEW_PEXELS_KEY')
    print("'TEST_SETTING'으로 값 설정...")
    settings_manager.set('TEST_SETTING', 12345)

    # 3. 설정된 값 확인 (메모리에서)
    print(f"메모리에서 PEXELS_API_KEY: {settings_manager.get('PEXELS_API_KEY')}")
    print(f"메모리에서 TEST_SETTING: {settings_manager.get('TEST_SETTING')}")

    # 4. 파일 저장 확인
    if os.path.exists(SETTINGS_FILE):
        print(f"\n'{SETTINGS_FILE}' 파일이 생성 또는 수정되었습니다.")
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            print("파일 내용:")
            print(f.read())
        # 테스트 후 파일 삭제
        os.remove(SETTINGS_FILE)
        print(f"\n테스트 완료 후 '{SETTINGS_FILE}' 파일 삭제됨.")
    else:
        print(f"\n오류: '{SETTINGS_FILE}' 파일이 생성되지 않았습니다.")

    print("\n--- 테스트 종료 ---")
