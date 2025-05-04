import os
import pandas as pd
import json

# ✅ 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "청원요지_GPT분류.csv")

# ✅ 키워드별 색상 정의 (프론트와 협의 필요)
CATEGORY_COLOR = {
    "정치·행정": "#1f77b4",
    "사회": "#ff7f0e",
    "경제·산업": "#2ca02c",
    "교육": "#d62728",
    "환경": "#9467bd",
    "교통·건설": "#8c564b",
    "보건·의료": "#e377c2",
    "문화·예술": "#7f7f7f",
    "과학·기술": "#bcbd22",
    "국방·외교": "#17becf",
    "기타": "#cccccc",
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
