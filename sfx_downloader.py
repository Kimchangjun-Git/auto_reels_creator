import os
import glob
import yt_dlp

def download_sfx(sfx_name, output_dir="assets/sfx"):
    """
    Downloads specific sound effects (SFX) if not present.
    Mapping common names to specific YouTube SFX videos (Copyright Free).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Dictionary of SFX names to YouTube Search Queries (or specific IDs if possible)
    # Using specific queries to find short, clean SFX
    sfx_map = {
        "whoosh": "whoosh transition sound effect no copyright",
        "pop": "pop sound effect no copyright",
        "camera": "camera shutter sound effect",
        "ding": "correct answer sound effect",
        "riser": "cinematic riser sound effect",
    }

    query = sfx_map.get(sfx_name, sfx_name + " sound effect")
    
    # Check if exists
    existing_files = []
    for ext in ['*.mp3', '*.m4a', '*.wav', '*.webm']:
        existing_files.extend(glob.glob(os.path.join(output_dir, f"{sfx_name}_*{ext}")))
    if existing_files:
        print(f"SFX '{sfx_name}' already exists.")
        return existing_files[0]
        
    print(f"Downloading SFX: {sfx_name}...")
    
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': os.path.join(output_dir, f'{sfx_name}_%(id)s.%(ext)s'),
        # Removing ffmpeg postprocessor dependency
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'match_filter': yt_dlp.utils.match_filter_func("duration < 30") # Only short clips
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"ytsearch1:{query}", download=True)
            
        # Find the downloaded file (any audio extension)
        downloaded = []
        for ext in ['*.mp3', '*.m4a', '*.wav', '*.webm']:
            downloaded.extend(glob.glob(os.path.join(output_dir, f"{sfx_name}_*{ext}")))
            
        if downloaded:
            return downloaded[0]
            
    except Exception as e:
        print(f"Failed to download SFX {sfx_name}: {e}")
        return None
        
if __name__ == "__main__":
    download_sfx("whoosh")
    download_sfx("pop")
