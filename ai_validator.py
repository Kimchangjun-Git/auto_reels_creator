import time
import google.generativeai as genai
import config
import json

from groq import Groq

def validate_media_relevance(script_context: str, media_metadata: dict, media_type: str = "video", provider="gemini") -> tuple[bool, str]:
    """Gemini or Groq (Llama 3) for media validation"""

    prompt = f"""
    You are a strict creative director for a Reels video.
    Check if the following {media_type} asset matches the script context.

    [Script Context]
    {script_context}

    [Media Metadata]
    {json.dumps(media_metadata, ensure_ascii=False)}

    Task:
    1. Evaluate if the media is relevant to the context.
    2. If YES, respond exactly with: {{"valid": true}}
    3. If NO (irrelevant, wrong mood, conflicting visuals), respond with a better SINGLE English search keyword to find the right media.
       Format: {{"valid": false, "suggestion": "better_keyword"}}
    
    Output JSON only.
    """

    # --- GROQ Implementation ---
    if provider == "groq":
        api_key = getattr(config, 'GROQ_API_KEY', None)
        if not api_key: return True, "No Groq Key" # Fail open
        
        try:
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a validator that outputs strictly JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            result = json.loads(completion.choices[0].message.content)
            if result.get('valid'): return True, "Suitable"
            else: return False, result.get('suggestion', 'abstract')
        except Exception as e:
            print(f"Groq Validation Error: {e}")
            return True, "Groq Error" # Fail open

    # --- GEMINI Implementation ---
    if not config.GEMINI_API_KEY:
        print("Warning: Gemini API Key가 없어 검증을 건너뜁니다.")
        return True, "No API Key"

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05') # Lite Model

    max_retries = 3
    base_delay = 10 # 10초 대기 (쿼터 회복)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            response_text = response.text.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(response_text)
                if result.get('valid'):
                    return True, "Suitable"
                else:
                    return False, result.get('suggestion', 'abstract')
            except json.JSONDecodeError:
                return True, "JSON Error" # Fail open
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg or "Quota" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"  ⚠️ Validation Quota Issue. {wait_time}초 대기... ({attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    print("Warning: AI 검증 쿼터 초과 (검증 생략 - 통과 처리)")
                    return True, "Quota Exceeded" # Fail open
            else:
                 print(f"AI Validation Error: {e}")
                 return True, "API Error"
