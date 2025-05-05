import os
import pandas as pd
import json

# ✅ 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "청원요지_GPT분류.csv")

# ✅ 키워드별 색상 정의 (프론트와 협의 필요)
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
    
    result = []
    for category, count in counts.items():
        result.append({
            "분야": category,
            "청원수": count,
            "색상": CATEGORY_COLOR.get(category, "#000000")
        })
    
    return result

if __name__ == "__main__":
    data = get_field_counts()
    print(json.dumps(data, ensure_ascii=False, indent=2))
