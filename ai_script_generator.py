import time
from google import genai
import json
import config
import os

from groq import Groq

def generate_script_with_groq(topic="재미있는 건강 상식", duration=30):
    """Groq API for Free/Fast inference"""
    api_key = getattr(config, 'GROQ_API_KEY', None)
    if not api_key or "YOUR_GROQ_API_KEY" in api_key:
        print("Groq API 키가 설정되지 않았습니다.")
        return None
        
    client = Groq(api_key=api_key)
    scene_count = max(3, int(duration / 5))
    
    prompt = f"""
    You are an expert Viral Content Creator for Instagram Reels.
    Create a {duration}s script about: "{topic}".
    
    Structure:
    1. Hook (0-3s): Visually shocking provided in 'visual_description' and 'visual_keywords'.
    2. Value: Core info.
    3. CTA: Call to action.

    Context:
    - Target Audience: Modern Koreans (MZ generation & general public).
    - Reflect current Korean culture, daily life patterns, and trending topics in Korea.
    - Use natural, conversational Korean (not translation-style).

    Return JSON ONLY:
    {{
        "metadata": {{ "topic": "{topic}", "total_duration_estimate": {duration}, "music_mood": "Upbeat" }},
        "scenes": [
            {{
                "scene_number": 1,
                "duration": 3,
                "visual_description": "Shocking visual...",
                "visual_keywords": ["shocking", "closeup"],
                "on_screen_text": "HOOK Text (*highlight*)",
                "narration": "Opening hook..."
            }}
        ]
    }}
    
    Constraints:
    - Narration & Text MUST BE IN KOREAN (한국어).
    - ABSOLUTELY NO Russian, Japanese, or Chinese characters (Hanja/한자).
    - If the topic suggests foreign content, TRANSLATE IT to Korean.
    - Visual keywords in ENGLISH.
    - Output pure JSON.
    """
    
    print(f"Groq Cloud (llama-3.3-70b)에게 대본 요청 중... (주제: {topic})")
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs strictly JSON. You MUST output Korean for text fields. No other languages allowed."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)
        
    except Exception as e:
        print(f"Groq Error: {e}")
        return None

def generate_script_with_ai(topic="재미있는 건강 상식", duration=30, provider="gemini"):
    """
    AI Provider Switcher (Gemini vs Groq).
    Uses the specified provider to generate the script.
    """
    if provider == "groq":
        print(f"Groq AI 에게 대본 요청 중... (주제: {topic})")
        return generate_script_with_groq(topic, duration)

    # Default to Gemini if provider is 'gemini' or something else
    script_data = None
    print(f"Gemini AI 에게 대본 요청 중... (주제: {topic})")
    api_key_gemini = getattr(config, 'GEMINI_API_KEY', None)

    if api_key_gemini and "YOUR_GEMINI_API_KEY" not in api_key_gemini:
        client = genai.Client(api_key=api_key_gemini)
        model_name = 'gemini-2.5-flash' 
        
        scene_count = max(3, int(duration / 5))

        prompt = f"""
        You are an expert Viral Content Creator for Instagram Reels & TikTok.
        Your goal is to create a "High Retention" video script about: "{topic}".
        Target Duration: {duration} seconds.
        
        ### VIral Structure Rule (MUST FOLLOW):
        1. **Scene 1 (The HOOK)**: 0-3 seconds. Must be visually shocking or ask a provocative question. Text must be short and punchy.
        2. **Middle Scenes (The VALUE)**: Deliver the core information fast. No fluff.
        3. **Final Scene (The CTA)**: Call to action. e.g., "Save this for later", "Share with a friend".

        ### Context:
        - Target Audience: Modern Koreans (MZ generation & general public).
        - Reflect current Korean culture, daily life patterns, and trending topics in Korea.
        - Use natural, conversational Korean (not translation-style).

        ### Output JSON Format:
        {{
            "metadata": {{
                "topic": "{topic}",
                "total_duration_estimate": {duration},
                "music_mood": "Upbeat" 
            }},
            "scenes": [
                {{
                    "scene_number": 1,
                    "duration": 3,
                    "visual_description": "A shocking or highly intriguing visual related to the topic. Closeup or fast motion.",
                    "visual_keywords": ["shocking", "intriguing", "closeup"],
                    "on_screen_text": "HOOK TEXT (Max 5 words, wrap keyword in *asterisks*)",
                    "narration": "Provocative opening sentence."
                }},
                ... (continue for total {scene_count} scenes)
            ]
        }}
        
        ### Constraints:
        1. **Language**: **MUST WRITE ALL 'narration' AND 'on_screen_text' IN KOREAN (한국어).**
        2. **Prohibition**: ABSOLUTELY NO Russian, Japanese, or Chinese characters (Hanja/한자).
        3. **Narration**: Conversational, fast-paced, and exciting. Max 40 characters per scene.
        4. **Visual Keywords**: ALWAYS use English. For the Hook, use specific, high-impact imagery.
        5. **On Screen Text**: Big, bold, short. No sentences, just impact phrases.
        6. **Music Mood**: Choose one: "Upbeat", "Phonk", "Suspense", "Energetic".
        """

        max_retries = 3
        base_delay = 10

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                text_response = response.text
                
                clean_json = text_response.replace('```json', '').replace('```', '').strip()
                script_data = json.loads(clean_json)
                
                if 'scenes' not in script_data:
                    print("AI 응답에 'scenes' 키가 없습니다.")
                    script_data = None
                else:
                    if 'metadata' not in script_data:
                        script_data['metadata'] = { "topic": topic }
                    
                    if 'music_mood' not in script_data['metadata']:
                        print("Warning: AI가 music_mood를 반환하지 않아 'Cheerful'로 설정합니다.")
                        script_data['metadata']['music_mood'] = "Cheerful"
                        
                    for i, scene in enumerate(script_data['scenes']):
                        if 'duration' not in scene:
                            print(f"  Warning: 장면 {i+1}에 'duration'이 없어 기본값(5)으로 설정합니다.")
                            scene['duration'] = 5
                        
                        if 'visual_keywords' not in scene or not isinstance(scene['visual_keywords'], list) or not scene['visual_keywords']:
                            print(f"  Warning: 장면 {i+1}에 'visual_keywords'가 유효하지 않아 기본값으로 대체합니다.")
                            desc = scene.get('visual_description', 'video')
                            scene['visual_keywords'] = [desc.split()[0]] if desc else ["general"]
                            
                        if 'narration' not in scene:
                            scene['narration'] = ""
                            
                        if 'on_screen_text' not in scene:
                            scene['on_screen_text'] = ""

                    print("Gemini 대본 생성을 성공적으로 완료하고 검증했습니다!")
                    break 
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "ResourceExhausted" in error_msg or "Quota" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"  ⚠️ Gemini Quota Exceeded. {wait_time}초 후 재시도합니다... ({attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("  ❌ Gemini 모든 재시도 실패. (무료 사용량 초과)")
                        script_data = None
                else:
                    print(f"Gemini 대본 생성 중 오류 발생: {e}")
                    script_data = None
            if script_data:
                break
    else:
        print("Gemini API 키가 설정되지 않았거나 유효하지 않습니다.")

    return script_data


def check_api_health(provider="gemini"):
    """
    API 쿼터 상태를 확인합니다. provider: 'gemini' or 'groq'
    """
    if provider == "groq":
        api_key = getattr(config, 'GROQ_API_KEY', None)
        if not api_key: return False, "Groq Key Missing"
        
        try:
            client = Groq(api_key=api_key)
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True, "Groq Status: Healthy 🟢"
        except Exception as e:
            return False, f"Groq Error: {str(e)}"
            
    else:
        # Gemini Check
        api_key = getattr(config, 'GEMINI_API_KEY', None)
        if not api_key: return False, "Gemini Key Missing"

        try:
            client = genai.Client(api_key=api_key)
            # Use a stable model for health check
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents="Hi",
                config={"max_output_tokens": 1}
            )
            if response: return True, "Gemini Status: Healthy 🟢"
            else: return False, "No Response"
        except Exception as e:
            if "429" in str(e) or "Quota" in str(e):
                return False, "⚠️ Gemini Quota Exceeded"
            return False, f"Gemini Error: {str(e)}"

if __name__ == "__main__":
    # 테스트
    # status, msg = check_api_health()
    # print(msg)
    
    result = generate_script_with_ai("직장인 거북목 교정 팁")
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
