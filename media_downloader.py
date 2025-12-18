from typing import Optional
import requests
import config
import os

def search_and_download_video(keyword: str, output_dir: str, duration: int) -> Optional[tuple[str, dict]]:
    """
    requests 라이브러리를 사용하여 Pexels API를 직접 호출하고,
    keyword에 맞는 세로형 영상을 검색하여 다운로드합니다.
    """
    if not config.PEXELS_API_KEY:
        print("Error: Pexels API Key가 설정되지 않았습니다.")
        return None, None

    headers = {
        "Authorization": config.PEXELS_API_KEY
    }
    
    params = {
        "query": keyword,
        "orientation": config.PEXELS_SEARCH_ORIENTATION,
        "size": config.PEXELS_SEARCH_SIZE,
        "per_page": config.PEXELS_SEARCH_PER_PAGE
    }

    try:
        print(f"Pexels API로 '{keyword}' 영상 검색 중...")
        response = requests.get(config.PEXELS_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Pexels API 요청 중 오류 발생: {e}")
        return None, None
    except Exception as e:
        print(f"Pexels API 응답 처리 중 오류 발생: {e}")
        return None, None

    if not data.get('videos'):
        print(f"'{keyword}'에 대한 세로형 영상을 찾을 수 없습니다. 키워드 단순화 시도 중...")
        # Self-Healing: 단어가 여러개면 마지막 단어로 재검색 시도
        words = keyword.split()
        if len(words) > 1:
            return search_and_download_video(words[-1], output_dir, duration)
        return None, None

    for video_item in data['videos']:
        # 다운로드할 비디오 파일 링크 선택
        selected_link = None
        best_quality = 0
        for file in video_item.get('video_files', []):
            # 1080p 이상 화질의 'hd' 링크를 우선적으로 찾음
            if file.get('quality') == 'hd' and file.get('height', 0) >= 1080 and file.get('link'):
                if file['height'] > best_quality:
                    selected_link = file['link']
                    best_quality = file['height']
        
        if selected_link:
            try:
                filename = f"{keyword.replace(' ', '_')}_{os.urandom(4).hex()}.mp4"
                filepath = os.path.join(output_dir, filename)
                
                print(f"'{keyword}' 영상 다운로드 중...")
                video_response = requests.get(selected_link, stream=True, timeout=30)
                video_response.raise_for_status()

                with open(filepath, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"'{keyword}' 영상 다운로드 완료: {filepath}")
                
                # 메타데이터 추출
                metadata = {
                    "query": keyword,
                    "tags": video_item.get('tags', []),
                    "url": video_item.get('url', ''),
                    "duration": video_item.get('duration', 0)
                }
                return filepath, metadata
            except requests.exceptions.RequestException as e:
                print(f"영상 파일 다운로드 중 오류 발생: {e}")
                continue # 다운로드 실패 시 다음 영상으로 넘어감
            except Exception as e:
                print(f"파일 저장 중 오류 발생: {e}")
                continue
    
    print(f"'{keyword}'에 대한 적합한 영상을 다운로드하지 못했습니다.")
    return None, None