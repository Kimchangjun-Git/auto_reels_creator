import moviepy.editor as mpe
import PIL.Image

print(f"Pillow version: {PIL.__version__}")

# Check for ANTIALIAS replacement
if not hasattr(PIL.Image, 'ANTIALIAS'):
    print("Monkey-patching Image.ANTIALIAS to Image.LANCZOS")
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import AudioFileClip
import os

# Create a dummy audio file
with open("dummy.mp3", "wb") as f:
    f.write(b"\x00" * 100)

try:
    # We might not be able to load a 0-byte file, but we can check the class
    methods = dir(AudioFileClip)
    print(f"AudioFileClip class has 'fl': {'fl' in methods}")
    print(f"AudioFileClip class has 'fl_audio': {'fl_audio' in methods}")
    print(f"AudioFileClip class has 'fl_image': {'fl_image' in methods}")
    print(f"AudioFileClip class has 'volumex': {'volumex' in methods}")
    print(f"AudioFileClip class has 'set_duration': {'set_duration' in methods}")
except Exception as e:
    print(f"Error checking methods: {e}")

if os.path.exists("dummy.mp3"):
    os.remove("dummy.mp3")
