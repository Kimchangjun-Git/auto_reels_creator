import os
import json
import time
from main import generate_script_pipeline, generate_video_pipeline

def process_batch(topics_file: str, provider: str = "gemini"):
    """
    여러 주제가 담긴 파일(txt)을 읽어 순차적으로 릴스를 생성합니다.
    """
    if not os.path.exists(topics_file):
        print(f"Error: {topics_file} 파일을 찾을 수 없습니다.")
        return

    with open(topics_file, 'r', encoding='utf-8') as f:
        topics = [line.strip() for line in f if line.strip()]

    print(f"🚀 총 {len(topics)}건의 배치 작업을 시작합니다.")
    
    results = []
    for i, topic in enumerate(topics):
        print(f"\n--- [{i+1}/{len(topics)}] 주제: {topic} ---")
        try:
            # 1. 스크립트 생성
            script_data = generate_script_pipeline("내우약", topic, 30, provider)
            if not script_data:
                print(f"❌ '{topic}' 스크립트 생성 실패")
                continue
            
            # 2. 영상 제작
            final_path = generate_video_pipeline(script_data)
            if final_path:
                print(f"✅ '{topic}' 생성 완료: {final_path}")
                results.append(final_path)
            else:
                print(f"❌ '{topic}' 영상 조립 실패")
                
        except Exception as e:
            print(f"❌ '{topic}' 처리 중 예상치 못한 오류: {e}")
        
        # API 쿼터 보호를 위한 짧은 휴식
        time.sleep(5)

    print(f"\n✨ 배치 작업 종료! 총 {len(results)}개의 영상이 생성되었습니다.")
    return results

if __name__ == "__main__":
    # 사용 예시: topics.txt 파일에 주제를 한 줄씩 적어두고 실행
    # process_batch("topics.txt")
    pass
