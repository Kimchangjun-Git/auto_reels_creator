from google import genai
import config
import os

api_key = getattr(config, 'GEMINI_API_KEY', None)
if not api_key:
    print("No API Key found")
else:
    client = genai.Client(api_key=api_key)
    print("Listing available models...")
    for m in client.models.list():
        print(f"Model Name: {m.name}")
        # print(f"  Supported methods: {m.supported_generation_methods}")
