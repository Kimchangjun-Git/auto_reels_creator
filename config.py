# config.py
import os
from settings_manager import settings_manager
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API Keys
# Priorities: 1. settings.json (via settings_manager) -> 2. Environment Variables (.env) -> 3. Default (for playground/dev)
PEXELS_API_KEY = settings_manager.get('PEXELS_API_KEY', os.getenv('PEXELS_API_KEY', ""))
GEMINI_API_KEY = settings_manager.get('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', ""))
GROQ_API_KEY = settings_manager.get('GROQ_API_KEY', os.getenv('GROQ_API_KEY', ""))

# Pexels API Settings
PEXELS_API_URL = "https://api.pexels.com/videos/search"
PEXELS_SEARCH_PER_PAGE = 15
PEXELS_SEARCH_ORIENTATION = "portrait"
PEXELS_SEARCH_SIZE = "large"

# Directory Settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DOWNLOADED_MEDIA_DIR = os.path.join(ASSETS_DIR, "downloaded_media")
NARRATION_AUDIO_DIR = os.path.join(ASSETS_DIR, "narration_audio")
FINAL_REELS_DIR = os.path.join(ASSETS_DIR, "final_reels")

# Reels Settings
REELS_WIDTH = settings_manager.get('REELS_WIDTH', 1080)
REELS_HEIGHT = settings_manager.get('REELS_HEIGHT', 1920)
REELS_FPS = settings_manager.get('REELS_FPS', 24)
REELS_CODEC = settings_manager.get('REELS_CODEC', "libx264")
REELS_AUDIO_CODEC = settings_manager.get('REELS_AUDIO_CODEC', "aac")

# Text Verification Settings
# Mac OS standard font path for Apple SD Gothic Neo 
FONT_PATH = settings_manager.get('FONT_PATH', "/System/Library/Fonts/AppleSDGothicNeo.ttc")
FONT_INDEX = settings_manager.get('FONT_INDEX', 1)
TARGET_FONT_INDEX = settings_manager.get('TARGET_FONT_INDEX', 8) # Apple SD Gothic Neo: Heavy weight

DEFAULT_FONT_SIZE = settings_manager.get('DEFAULT_FONT_SIZE', 100) # 더 크게 조정
TEXT_COLOR = settings_manager.get('TEXT_COLOR', 'white')
TEXT_STROKE_COLOR = settings_manager.get('TEXT_STROKE_COLOR', 'black')
TEXT_STROKE_WIDTH = settings_manager.get('TEXT_STROKE_WIDTH', 4) # 테두리 가독성 확보
HIGHLIGHT_TEXT_COLOR = settings_manager.get('HIGHLIGHT_TEXT_COLOR', 'yellow')
TEXT_POSITION_Y_RATIO = settings_manager.get('TEXT_POSITION_Y_RATIO', 0.7) # 자막 위치를 위로 올림 (0.7 ~ 0.8 추천)

TEXT_BG_ENABLED = settings_manager.get('TEXT_BG_ENABLED', True)
TEXT_BG_COLOR = settings_manager.get('TEXT_BG_COLOR', (0, 0, 0, 180)) # 가독성 위해 조금 더 어둡게
TEXT_BG_PADDING = settings_manager.get('TEXT_BG_PADDING', 40)
TEXT_BORDER_RADIUS = settings_manager.get('TEXT_BORDER_RADIUS', 25)

# TTS Settings
TTS_VOICE = settings_manager.get('TTS_VOICE', "ko-KR-SunHiNeural")
TTS_RATE = settings_manager.get('TTS_RATE', "+25%")

# Audio Ducking Settings
BGM_DUCK_VOLUME = settings_manager.get('BGM_DUCK_VOLUME', 0.1)
BGM_NORMAL_VOLUME = settings_manager.get('BGM_NORMAL_VOLUME', 0.35)

# Performance & Robustness (Roadmap 4)
GPU_ACCELERATION = settings_manager.get('GPU_ACCELERATION', False) # 충돌 방지를 위해 확실히 꺼둠
FFMPEG_VIDEO_CODEC = "h264_videotoolbox" if GPU_ACCELERATION else "libx264"