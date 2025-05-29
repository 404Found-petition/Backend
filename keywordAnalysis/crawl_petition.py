import os
import time
import pandas as pd
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from django.conf import settings

CSV_PATH = os.path.join(os.path.dirname(__file__), '병합된_청원_데이터.csv')

def get_petition_summary(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            summary_element = soup.select_one("div.textType02#summaryContentDiv")
            if summary_element:
                return summary_element.text.strip()
        return None
    except Exception as e:
        print(f"❌ 크롤링 오류: {e}")
        return None

def fetch_petition_data(api_key, start_eraco=13, end_eraco=22):
    base_url = "https://open.assembly.go.kr/portal/openapi/PTTRCP"
    all_data = []

    for d in range(start_eraco, end_eraco + 1):
        eraco = f"제{d}대"
        p_index = 1
        print(f"📥 수집 중: {eraco}")
        while True:
            params = {
                "KEY": settings.OPENCONGRESS_KEY,
                "Type": "json",
                "pIndex": p_index,
                "pSize": 100,
                "ERACO": eraco
            }
            try:
                response = requests.get(base_url, params=params)
                if response.status_code != 200:
                    print(f"❌ 요청 실패 (ERACO={eraco}, pIndex={p_index})")
                    break

                response_json = response.json()
                pttrcp_data = response_json.get("PTTRCP", [])
                result = []
                for section in pttrcp_data:
                    if isinstance(section, dict) and "row" in section:
                        result = section["row"]
                        break

                if not result:
                    break

                all_data.extend(result)
                p_index += 1
                time.sleep(0.2)

            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                break

    return all_data

def main():
    api_key = settings.OPENCONGRESS_KEY  # 안전하게 .env나 환경변수로 관리 권장
    data = fetch_petition_data(api_key)
    df = pd.DataFrame(data)

    if "LINK_URL" in df.columns:
        df["링크URL"] = df["LINK_URL"]
        summaries = []
        for url in tqdm(df["링크URL"]):
            summaries.append(get_petition_summary(url) or "")
        df["청원요지"] = summaries

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"✅ 저장 완료: {CSV_PATH}")

# 외부에서 import해서 main()을 실행할 수 있도록
if __name__ == "__main__":
    main()
