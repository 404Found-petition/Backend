from .models import FieldSummary
import pandas as pd
import os

# 색상 정의
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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, "청원요지_GPT분류.csv")

    df = pd.read_csv(csv_path)
    df["분야"] = df["분야"].fillna("기타")

    counts = df["분야"].value_counts().sort_values(ascending=False)

    result = []
    for category, count in counts.items():
        result.append({
            "분야": category,
            "청원수": count,
            "색상": CATEGORY_COLOR.get(category, "#000000")
        })
    return result

def store_field_counts_in_db():
    data = get_field_counts()
    for item in data:
        FieldSummary.objects.update_or_create(
            분야=item["분야"],
            defaults={
                "청원수": item["청원수"],
                "색상": item["색상"]
            }
        )