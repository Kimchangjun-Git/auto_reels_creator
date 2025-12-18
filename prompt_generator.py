# prompt_generator.py

class PromptGenerator:
    """
    Gemini 모델의 기자 적합성 평가를 위한 프롬프트를 생성하는 클래스입니다.
    """
    @staticmethod
    def generate_evaluation_prompt(
        app_description: str,
        app_pr_points: str,
        media_outlet: str,
        reporter_affiliation: str,
        reporter_name: str,
        article_url: str = None,
        article_content: str = None
    ) -> str:
        """
        기자 적합성 평가를 위한 프롬프트 문자열을 생성합니다.
        
        Args:
            app_description (str): 앱 설명.
            app_pr_points (str): 앱의 핵심 홍보 포인트.
            media_outlet (str): 언론사명.
            reporter_affiliation (str): 기자의 소속/전문 분야.
            reporter_name (str): 기자 이름.
            article_url (str, optional): 최신 기사 URL. 기본값은 None.
            article_content (str, optional): 최신 기사 내용. 기본값은 None.
            
        Returns:
            str: Gemini 모델에 전달할 프롬프트 문자열.
        """
        article_url_str = article_url if article_url else "없음"
        article_content_str = article_content if article_content else "없음"

        prompt = f"""
**Role**: 당신은 "내우약" 앱의 홍보 전략 전문가입니다.
**Task**: 주어진 앱 정보와 기자 정보를 바탕으로 해당 기자가 "내우약" 앱 홍보에 얼마나 적합한지 평가하고 0점에서 100점 사이의 점수와 간략한 평가 근거를 제시해 주세요.

---
**내우약 앱 정보:**
**앱 설명:**
{app_description}

**핵심 홍보 포인트:**
{app_pr_points}

---
**기자 정보:**
**언론사:** {media_outlet}
**소속/전문 분야:** {reporter_affiliation}
**기자 이름:** {reporter_name}
**최신 기사 URL (존재하는 경우):** {article_url_str}
**기사 내용 (존재하는 경우):**
{article_content_str}
---

**평가 기준:**
*   기자의 소속/전문 분야가 앱의 내용과 얼마나 관련이 깊은가?
*   (향후) 기사의 내용이 앱의 주제와 얼마나 일치하는가?
*   전반적인 홍보 효과 기대치.

**지시:**
1.  0점에서 100점 사이의 적합성 점수를 산출합니다. (0점: 전혀 부적합, 100점: 완벽하게 적합)
2.  점수와 함께 3문장 이내의 간략한 평가 근거를 제시합니다.
3.  응답은 JSON 형식으로만 제공해야 합니다.
    ```json
    {{
      "score": [점수],
      "reason": "[평가 근거]"
    }}
    ```
"""
        return prompt.strip()

if __name__ == '__main__':
    # Example Usage
    app_desc = "내우약 앱은 가정 상비약의 유효기간을 관리하고, 영양제 복용 알림을 제공하는 스마트 건강 관리 애플리케이션입니다."
    app_pr = "직관적인 유효기간 관리; 맞춤형 영양제 알림; 가족 건강 관리"
    
    # Test case 1: Basic prompt generation
    prompt1 = PromptGenerator.generate_evaluation_prompt(
        app_description=app_desc,
        app_pr_points=app_pr,
        media_outlet="연합뉴스",
        reporter_affiliation="경제",
        reporter_name="홍규빈"
    )
    print("--- Basic Prompt Example ---")
    print(prompt1)
    print("\n" + "="*50 + "\n")

    # Test case 2: Prompt with article URL and content
    prompt2 = PromptGenerator.generate_evaluation_prompt(
        app_description=app_desc,
        app_pr_points=app_pr,
        media_outlet="지디넷코리아",
        reporter_affiliation="IT/과학",
        reporter_name="류승현",
        article_url="http://www.zdnet.co.kr/view/?no=20231026101010",
        article_content="최신 IT 기술 동향과 스마트 헬스케어 관련 기사 내용입니다."
    )
    print("--- Prompt with Article Info Example ---")
    print(prompt2)
    print("\n" + "="*50 + "\n")

    # Test case 3: Check JSON format instruction
    assert '```json' in prompt1
    assert '"score": [점수],' in prompt1
    print("JSON format instruction is correctly included.")
