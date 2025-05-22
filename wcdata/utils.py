import os
import pandas as pd
from konlpy.tag import Okt
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from petition.gov.models import MonthlyKeyword
from datetime import datetime

# ✅ 불용어 목록
STOPWORDS = set([
    "청원", "요청", "의원", "정부", "국민", "관련", "문제", "조치", "대책", "해결", "필요",
    "부탁", "보장", "의혹", "언제", "통해", "일치", "검토", "확인", "요구", "마련", "처리",
    "사항", "위해", "위한", "대한", "있도록", "합니다", "대한민국", "국가", "국내", "발의",
    "개인", "제한", "영향", "안정", "해당", "정책", "우려", "활동", "사례", "우선", "작성",
    "활용", "모든", "위협", "또한", "대해", "정의", "근거", "상황", "정성", "야기", "다수",
    "주요", "효과", "도입", "방법", "적용", "진행", "최근", "전면", "판단", "유지", "과정",
    "각종", "원래", "현재", "취지", "체제", "존속", "당초", "발전"
])

# ✅ CSV 파일 경로
CSV_PATH = os.path.join(os.path.dirname(__file__), "병합된_청원_데이터.csv")

# ✅ 청원 데이터 로딩 및 월별 컬럼 생성
def load_monthly_data():
    df = pd.read_csv(CSV_PATH)
    df["등록일"] = pd.to_datetime(df["RCP_DT"], errors="coerce")
    df["월"] = df["등록일"].dt.to_period("M").astype(str)
    return df

# 청원 요지 추출 위한 간단한 요약 함수
def get_petition_summary(text, max_len=300):
    if not isinstance(text, str):
        return ""
    summary = text.strip().replace("\n", " ")
    return summary[:max_len] + "..." if len(summary) > max_len else summary


# ✅ 사용 가능한 월 목록 반환
def get_available_months():
    df = load_monthly_data()
    return sorted(df["월"].dropna().unique())

# ✅ 단순 빈도 기반 키워드 추출
def extract_keywords_by_month(month):
    df = load_monthly_data()
    df = df[df["월"] == month]
    if df.empty:
        return []

    texts = (df["PTT_NM"].fillna("") + " " + df["청원요지"].fillna("")).tolist()
    okt = Okt()
    joined = " ".join(texts)
    nouns = [w for w in okt.nouns(joined) if 2 <= len(w) <= 5 and w not in STOPWORDS]
    counter = Counter(nouns)
    return [{"word": w, "count": c} for w, c in counter.most_common(100)]

# ✅ TF-IDF 기반 키워드 중요도 추출
def extract_keywords_by_month_tfidf(month):
    df_all = load_monthly_data()
    if month not in df_all["월"].unique():
        return []

    okt = Okt()
    monthly_docs = []
    for _, group in df_all.groupby("월"):
        texts = (group["PTT_NM"].fillna("") + " " + group["청원요지"].fillna("")).tolist()
        joined_text = " ".join(texts)
        nouns = [word for word in okt.nouns(joined_text) if 2 <= len(word) <= 5 and word not in STOPWORDS]
        monthly_docs.append(" ".join(nouns))

    vectorizer = TfidfVectorizer(token_pattern=r"[가-힣]{2,5}")
    tfidf_matrix = vectorizer.fit_transform(monthly_docs)
    feature_names = vectorizer.get_feature_names_out()

    months = sorted(df_all["월"].unique())
    idx = months.index(month)
    scores = tfidf_matrix[idx].toarray().flatten()

    tfidf_dict = dict(zip(feature_names, scores))
    top_words = sorted(tfidf_dict.items(), key=lambda x: x[1], reverse=True)[:100]
    return [{"word": w, "score": round(s, 4)} for w, s in top_words if w not in STOPWORDS]

def store_keywords_in_db():
    from petition.gov.models import MonthlyKeyword
    import pandas as pd
    from konlpy.tag import Okt
    from collections import Counter

    # ✅ CSV 로드
    df = pd.read_csv("wcdata/병합된_청원_데이터.csv")

    # ✅ 날짜 파싱 및 월 컬럼 생성 (NaT 제거 포함)
    df["등록일"] = pd.to_datetime(df["RCP_DT"], errors="coerce")
    df = df[df["등록일"].notna()]  # NaT 제거
    df["월"] = df["등록일"].dt.to_period("M").astype(str)  # "2024-04" 형식으로 변환

    # ✅ 기존 DB 데이터 삭제
    MonthlyKeyword.objects.all().delete()

    okt = Okt()

    for month, group in df.groupby("월"):
        texts = (group["PTT_NM"].fillna("") + " " + group["청원요지"].fillna("")).tolist()
        joined = " ".join(texts)
        nouns = [w for w in okt.nouns(joined) if 2 <= len(w) <= 5]
        counter = Counter(nouns)

        for word, count in counter.most_common(100):
            MonthlyKeyword.objects.update_or_create(
                month=month,
                keyword=word,
                defaults={"score": count}
            )
