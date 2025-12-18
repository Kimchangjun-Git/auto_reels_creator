import os
import glob
import yt_dlp
import random

def download_bgm(output_dir="assets/music", mood="Cheerful"):
    """
    assets/music 폴더에 해당 무드(Mood)에 맞는 BGM이 없으면 다운로드합니다.
    """
    # 1. 디렉토리 확인 및 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 2. 이미 해당 무드의 파일이 있는지 확인 (파일명에 mood 포함된 것)
    # 예: bgm_Sad_videoID.mp3
    existing_files = []
    # 단순화를 위해 모든 오디오 파일 검색 후, 파일명에 mood가 포함되어 있는지 확인하거나
    # 아니면 매번 새로 받는 게 낫나? -> 쿼터 절약을 위해 있으면 씀.
    # 하지만 유저가 매번 다른 느낌을 원할 수 있으니...
    # 일단 'bgm_{mood}_' 패턴이 있는지 확인.
    
    for ext in ['*.mp3', '*.m4a', '*.wav', '*.webm']:
        for filepath in glob.glob(os.path.join(output_dir, ext)):
            filename = os.path.basename(filepath)
            if f"bgm_{mood}_" in filename:
                existing_files.append(filepath)
        
    if existing_files:
        print(f"[{mood}] 무드의 BGM 파일이 이미 존재합니다: {existing_files[0]}")
        # 기존 파일은 메타데이터를 알 수 없으므로(파일명만 있음), 간단히 반환
        return existing_files[0], {"source": "existing", "filename": os.path.basename(existing_files[0])}

    print(f"[{mood}] 무드의 BGM 파일이 없습니다. 유튜브에서 다운로드를 시작합니다...")
    
    # 3. yt-dlp 옵션 설정
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best', # m4a 우선 (호환성), 없으면 best
        # 파일명에 mood 포함
        'outtmpl': os.path.join(output_dir, f'bgm_{mood}_%(id)s.%(ext)s'),
        # postprocessors (FFmpegExtractAudio) 제거 -> 시스템 ffmpeg 의존성 제거
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }

    # 검색어 생성
    search_query = f"No copyright background music {mood}"
    search_url = f"ytsearch1:{search_query}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"검색어: '{search_query}' 다운로드 중...")
            info_dict = ydl.extract_info(search_url, download=True)
            
            # 다운로드된 파일명 찾기 (정확한 경로 반환을 위해)
            # yt-dlp는 확정된 확장자를 info_dict['ext']에 담음
            if 'entries' in info_dict:
                video_info = info_dict['entries'][0]
            else:
                video_info = info_dict
            
            # 실제 다운로드된 파일 확인 (확장자가 mp3가 아닐 수 있음)
            # 가장 확실한 건 glob으로 찾는 것
            video_id = video_info['id']
            potential_files = glob.glob(os.path.join(output_dir, f"bgm_{mood}_{video_id}.*"))
            if potential_files:
                downloaded_path = potential_files[0]
                print(f"BGM 다운로드 완료: {downloaded_path}")
                
                metadata = {
                    "title": video_info.get('title', ''),
                    "tags": video_info.get('tags', []),
                    "description": video_info.get('description', '')[:200], # 너무 길면 자름
                    "mood_query": mood
                }
                return downloaded_path, metadata
            
            return None, None
            
    except Exception as e:
        print(f"BGM 다운로드 실패: {e}")
        return None, None

if __name__ == "__main__":
    download_bgm()
