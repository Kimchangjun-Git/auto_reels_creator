# debug_env.py
import sys
import os

print("--- Python Environment Debug ---")
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")

print("\n--- sys.path ---")
for path in sys.path:
    print(path)

print("\n--- moviepy import test ---")
try:
    import moviepy
    print("Successfully imported 'moviepy'")
    print(f"moviepy version: {moviepy.__version__}")
    print(f"moviepy path: {moviepy.__file__}")
    
    # moviepy.editor가 있는지 확인
    editor_path = os.path.join(os.path.dirname(moviepy.__file__), 'editor.py')
    print(f"Expected editor.py path: {editor_path}")
    print(f"Does editor.py exist? {os.path.exists(editor_path)}")
    
    from moviepy.editor import VideoFileClip
    print("Successfully imported 'VideoFileClip' from 'moviepy.editor'")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("\n--- Debugging Finished ---")

