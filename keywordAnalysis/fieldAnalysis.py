import os
import time
import openai
import pandas as pd
from django.conf import settings

# ✅ 환경 변수 또는 settings.py에서 API 키 로드
openai.api_key = settings.GPT_KEY

# ✅ 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "병합된_청원_데이터.csv")
CSV_OUTPUT = os.path.join(BASE_DIR, "청원요지_GPT분류.csv")

# ✅ GPT 기반 분야 분류 함수
def classify_with_gpt_by_summary(summary_text):
    prompt = f"""
## 작업할 일
- 다음 청원의 요지를 읽고 아래 11개 중 가장 정확한 하나의 분야로 분류하세요

## 분야 목록
- 분야목록: [정치·행정, 사회, 경제·산업, 교육, 환경, 교통·건설, 보건·의료, 문화·예술, 과학·기술, 국방·외교, 기타]

## 입력
청원요지: "{summary_text}"

## 출력
- 무조건 주어진 분야 중에 하나로 출력하세요.
- 출력 예시: "사회"
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        result = response["choices"][0]["message"]["content"].strip()
        return result.replace("분야:", "").strip()
    except Exception as e:
        print(f"❌ GPT 요청 오류: {e}")
        return "기타"

def main():
    df = pd.read_csv(CSV_INPUT)
    df["청원요지"] = df["청원요지"].fillna("")
    df["분야"] = df["청원요지"].apply(lambda x: classify_with_gpt_by_summary(x) if x.strip() else "기타")
    df.to_csv(CSV_OUTPUT, index=False, encoding="utf-8-sig")
    print(f"✅ 분야 분류 완료: {CSV_OUTPUT}")

if __name__ == "__main__":
    main()
