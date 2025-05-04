import requests
from bs4 import BeautifulSoup

# 테스트할 청원 URL
test_url = "https://likms.assembly.go.kr/bill/billDetail.do?billId=PRC_U2O4Q1L0W0A7L1U6J5M5B3W8M5J4G4"

# 요청 보내기
response = requests.get(test_url, headers={"User-Agent": "Mozilla/5.0"})

# HTML 응답이 정상적으로 왔는지 확인
if response.status_code == 200:
    # BeautifulSoup을 사용하여 HTML 파싱
    soup = BeautifulSoup(response.text, "html.parser")

    # HTML의 앞부분 일부 출력하여 구조 확인 (너무 많으면 분석이 어려우므로 3000자만 출력)
    html_preview = response.text[:3000]
    print(html_preview)  # 로컬에서 실행 시 HTML 미리보기
else:
    print(f"❌ 요청 실패, 상태 코드: {response.status_code}")