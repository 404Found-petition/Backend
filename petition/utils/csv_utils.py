'''
csv 관련 함수 모음집
'''
import os
import pandas as pd
from django.conf import settings
from petition.gov.models import PredictionResult, MonthlyKeyword
from wcdata.utils import load_monthly_data, get_petition_summary, extract_keywords_by_month
from keywordAnalysis.models import PetitionSummary

# 아래 3개 청원 동의 현황 페이지용
# ✅ 원본 데이터를 받아 CSV로 저장
def save_data_to_csv(data, filename='원본데이터.csv'):
    path = os.path.join(settings.BASE_DIR, 'AI', filename)
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding='utf-8-sig')

# ✅ DB 데이터를 CSV로 export
def export_predictions_to_csv(filename='db_exported_predictions.csv'):
    path = os.path.join(settings.BASE_DIR, 'AI', filename)
    queryset = PredictionResult.objects.all()
    df = pd.DataFrame(list(queryset.values()))
    df.to_csv(path, index=False, encoding='utf-8-sig')

# ✅ AI 예측결과를 CSV로 저장
def save_prediction_to_csv(predictions, filename='예측결과.csv'):
    path = os.path.join(settings.BASE_DIR, 'AI', filename)
    df = pd.DataFrame(predictions)
    df.to_csv(path, index=False, encoding='utf-8-sig')

# 아래 4개 워드클라우드용    
# ✅ CSV 저장 함수
def to_csv(dataframe, filename):
    path = os.path.join(settings.BASE_DIR, 'AI', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dataframe.to_csv(path, index=False, encoding='utf-8-sig')
    
# ✅ 요약 CSV + DB 저장
def save_summary_csv_and_db(df, filename="청원_요약본.csv"):
    path = os.path.join(settings.BASE_DIR, "AI", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")

    for _, row in df.iterrows():
        PetitionSummary.objects.update_or_create(
            title=row["PTT_NM"],
            summary=row["청원요지"],
            created_at=row["등록일"]
        )
    
# ✅ 키워드 CSV를 DB로 저장
def load_keywords_from_csv_to_db(filename):
    path = os.path.join(settings.BASE_DIR, 'AI', filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {path}")
    
    df = pd.read_csv(path)
    required = {'월', '단어', '중요도'}
    if not required.issubset(df.columns):
        raise ValueError(f"CSV에 필요한 컬럼 없음: {required}")

    for _, row in df.iterrows():
        MonthlyKeyword.objects.update_or_create(
            month=row['월'],
            keyword=row['단어'],
            defaults={'score': row['중요도']}
        )

# ✅ 전체 요약 흐름 실행 (분석 + 저장)
def summarize_and_store():
    df = load_monthly_data()
    df["청원요지"] = df["청원내용"].apply(get_petition_summary)
    summary_df = df[["PTT_NM", "청원요지", "등록일"]]
    save_summary_csv_and_db(summary_df)

