# gemini_evaluator.py
import os
import time # Added for sleep in retry logic
from google import genai
import json
import config # Import config module
from groq import Groq # Import Groq
from prompt_generator import PromptGenerator

class GeminiEvaluator:
    """
    Gemini 모델을 사용하여 기자 적합성을 평가하는 클래스입니다.
    Gemini API 호출 실패 시 Groq API를 폴백으로 사용합니다.
    """
    def __init__(self, model_name: str = "gemini-pro-latest"):
        # Gemini setup is done on demand in evaluate_reporter_suitability due to fallback logic
        self.gemini_model_name = model_name
        self.groq_client = None # Initialize Groq client later if needed

    def _call_gemini_api(self, prompt: str) -> dict:
        """Internal helper to call Gemini API - currently disabled, always returns empty dict."""
        print("DEBUG: _call_gemini_api called (Gemini API disabled).")
        # Forcibly disable Gemini API calls as per user request
        print("Warning: Gemini API 호출은 사용자 요청에 의해 비활성화되었습니다. Groq 폴백을 시도합니다.")
        return {}

    def _call_groq_api(self, prompt: str) -> dict:
        """Internal helper to call Groq API with retry mechanism."""
        print("DEBUG: _call_groq_api called.")
        api_key = config.GROQ_API_KEY
        if not api_key or "YOUR_GROQ_API_KEY" in api_key:
            print("Warning: Groq API 키가 설정되지 않았습니다. Groq 호출 건너뛰기.")
            return {}

        max_retries = 3
        base_delay = 5 # seconds

        for attempt in range(max_retries):
            try:
                if not self.groq_client:
                    self.groq_client = Groq(api_key=api_key)
                
                print(f"DEBUG: Calling Groq chat.completions.create (Attempt {attempt + 1}/{max_retries})...")
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that evaluates reporter suitability. You MUST output JSON with 'score' (int) and 'reason' (string) fields. No other languages allowed."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500,
                    top_p=1,
                    stream=False,
                    response_format={"type": "json_object"}
                )
                print("DEBUG: Groq chat.completions.create responded.")
                
                response_text = completion.choices[0].message.content
                evaluation_result = json.loads(response_text)

                if "score" in evaluation_result and "reason" in evaluation_result:
                    print(f"DEBUG: Groq API call successful on attempt {attempt + 1} and response parsed.")
                    return evaluation_result
                else:
                    print(f"Warning: Groq response missing 'score' or 'reason' keys on attempt {attempt + 1}: {evaluation_result}")
                    return {} # Consider this a failure for the current attempt

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Rate limit" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"  ⚠️ Groq Rate Limit Exceeded. {wait_time}초 후 재시도합니다... (시도 {attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ❌ 모든 Groq 재시도 실패. (Rate Limit 초과)")
                        return {}
                else:
                    print(f"ERROR: Groq API call failed with exception on attempt {attempt + 1}: {e}")
                    return {} # Other errors are immediate failures

        print("DEBUG: All Groq attempts failed. Returning empty result.")
        return {} # Should not be reached if max_retries is > 0 and a path always returns


    def evaluate_reporter_suitability(self, prompt: str) -> dict:
        """
        주어진 프롬프트를 사용하여 기자 적합성 평가를 요청합니다.
        Gemini 모델을 우선 사용하고, 실패 시 Groq 모델로 폴백합니다.
        """
        evaluation_result = {}
        
        # 1. Try Gemini first
        print("Gemini API로 기자 적합성 평가 시도 중...")
        evaluation_result = self._call_gemini_api(prompt)

        # Consider both empty dict or score is None as failure to get valid result
        if not evaluation_result or evaluation_result.get("score") is None: 
            print("Gemini 평가 실패 또는 유효하지 않은 결과. Groq API로 폴백 시도 중...")
            evaluation_result = self._call_groq_api(prompt)
            if evaluation_result and evaluation_result.get("score") is not None:
                print("Groq API로 평가 성공.")
                return evaluation_result
            else:
                print("Groq API 평가도 실패했습니다.")
        elif evaluation_result.get("score") is not None:
            print("Gemini API로 평가 성공.")
            return evaluation_result
        
        # Default fallback if both fail
        print("DEBUG: Both Gemini and Groq evaluation failed. Returning default.")
        return {"score": 0, "reason": "AI 평가 실패"}


if __name__ == '__main__':
    print("--- GeminiEvaluator Class Example ---")

    # For testing, check API keys but do not modify config directly
    if not config.GEMINI_API_KEY or "YOUR_GEMINI_API_KEY" in config.GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY in config.py is not set to a real key. AI evaluations will likely fail.")
    
    if not config.GROQ_API_KEY or "YOUR_GROQ_API_KEY" in config.GROQ_API_KEY:
        print("Warning: GROQ_API_KEY in config.py is not set to a real key. Groq fallback will likely fail.")


    evaluator = GeminiEvaluator()

    app_desc = "내우약 앱은 가정 상비약의 유효기간을 관리하고, 영양제 복용 알림을 제공하는 스마트 건강 관리 애플리케이션입니다."
    app_pr = "직관적인 유효기간 관리; 맞춤형 영양제 알림; 가족 건강 관리"
    
    # Generate a sample prompt
    sample_prompt = PromptGenerator.generate_evaluation_prompt(
        app_description=app_desc,
        app_pr_points=app_pr,
        media_outlet="연합뉴스",
        reporter_affiliation="경제",
        reporter_name="홍규빈"
    )

    print("\nGenerated Sample Prompt (first 200 chars):")
    print(sample_prompt[:200] + "...")

    # Evaluate (this will call the actual API if key is real)
    print("\n--- Calling AI for Evaluation ---")
    evaluation_result = evaluator.evaluate_reporter_suitability(sample_prompt)

    print("\nAI Evaluation Result:")
    print(evaluation_result)

    # Expected format check (for real API calls, this would be more robust)
    if evaluation_result and isinstance(evaluation_result.get("score"), int) and isinstance(evaluation_result.get("reason"), str):
        print("\nEvaluation result format looks correct.")
    else:
        print("\nEvaluation result format is not as expected.")