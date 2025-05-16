import os
import pandas as pd
import json
from keywordAnalysis.models import PetitionSummaryCategory
from .fieldAnalysis import classify_with_gpt_by_summary  # GPT 분류 함수

# CSV 저장 함수 직접 정의 (csv_utils 대체)
def to_csv(df, filename):
    df.to_csv(filename, index=False, encoding="utf-8-sig")

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "청원요지_GPT분류.csv")

CATEGORY_COLOR = {
    "정치·행정": "#70B7FF",
    "사회": "#B1FF9A",
    "경제·산업": "#F2B856",
    "교육": "#FFF12B",
    "환경": "#42D583",
    "교통·건설": "#F9A3D4",
    "보건·의료": "#FF5A4E",
    "문화·예술": "#CBA0FF",
    "과학·기술": "#33E4FF",
    "국방·외교": "#538F2D",
    "기타": "#AAAAAA",
}

def get_field_counts():
    df = pd.read_csv(CSV_INPUT)
    counts = df["분야"].value_counts().sort_values(ascending=False)
    return [
        {"분야": category, "청원수": count, "색상": CATEGORY_COLOR.get(category, "#000000")}
        for category, count in counts.items()
    ]

def save_to_db(df):
    for _, row in df.iterrows():
        PetitionSummaryCategory.objects.create(
            청원제목=row.get("청원제목", "")[:255],
            청원요지=row.get("청원요지", ""),
            분야=row.get("분야", "")
        )

def main():
    df = pd.read_csv(CSV_INPUT)
    df["청원요지"] = df["청원요지"].fillna("")
    df["분야"] = df["청원요지"].apply(lambda x: classify_with_gpt_by_summary(x) if x.strip() else "기타")
    to_csv(df, "청원요지_GPT분류.csv")
    save_to_db(df)
    print("✅ 모든 저장 완료")

if __name__ == "__main__":
    main()
    data = get_field_counts()
    print(json.dumps(data, ensure_ascii=False, indent=2))
