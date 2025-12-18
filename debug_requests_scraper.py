
import requests
from bs4 import BeautifulSoup

def main():
    # 실제 브라우저처럼 보이기 위한 User-Agent 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # 테스트할 언론사 ID
    office_id = '001'
    url = f"https://media.naver.com/journalists/whole?officeId={office_id}"

    try:
        print(f"Requests 라이브러리로 URL에 접근합니다: {url}")
        # 타임아웃을 10초로 설정
        response = requests.get(url, headers=headers, timeout=10)
        # HTTP 오류 발생 시 예외 발생
        response.raise_for_status()

        print(f"HTTP 상태 코드: {response.status_code}")

        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # Playwright 스크립트에서 사용했던 선택자로 요소 검색
        media_outlet_element = soup.select_one("span._journalist_office_name")
        journalist_items = soup.select("li.journalist_list_content_item")

        print(f"언론사 이름: {media_outlet_element.text.strip() if media_outlet_element else '찾을 수 없음'}")
        print(f"기자 목록 수: {len(journalist_items)}")

        # 기자 정보가 있다면 첫 번째 기자 이름 출력
        if journalist_items:
            first_item = journalist_items[0]
            name_element = first_item.select_one("a.journalist_list_content_name")
            print(f"첫 번째 기자 이름: {name_element.text.strip() if name_element else 'N/A'}")
        else:
            print("기자 목록을 찾을 수 없습니다. 콘텐츠가 동적으로 로드되는 것 같습니다.")

    except requests.exceptions.RequestException as e:
        print(f"요청 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
