import os
import pandas as pd
import numpy as np
import joblib
from tqdm import tqdm
import torch
from transformers import AutoTokenizer, AutoModel

# ====================
# 1️⃣ 환경 및 모델 설정
# ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("📂 현재 작업 디렉토리:", BASE_DIR)

# 모델 경로 설정
model_path = os.path.join(BASE_DIR, '청원_예측모델.pkl')
scaler_path = os.path.join(BASE_DIR, 'scaler.pkl')
csv_path = os.path.join(BASE_DIR, '진행중국민동의청원현황.csv')
crawl_path = os.path.join(BASE_DIR, '청원_처리_현황_크롤링완료.csv')
output_path = os.path.join(BASE_DIR, '예측결과.csv')

# ======================
# 2️⃣ 모델 및 데이터 불러오기
# ======================
try:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print("✅ 모델 불러오기 성공!")
except Exception as e:
    print(f"❌ 모델 불러오기 실패: {e}")
    exit()

try:
    df = pd.read_csv(csv_path, encoding="cp949")
    print(f"✅ 진행 중 청원 {len(df)}개 로드 성공")
except Exception as e:
    print(f"❌ 청원 데이터 로드 실패: {e}")
    df = pd.DataFrame(columns=["청원제목", "청원내용"])

try:
    df_crawl = pd.read_csv(crawl_path, encoding="utf-8")
    df = df.merge(df_crawl[["청원제목", "청원내용"]], on="청원제목", how="left")
    print("✅ 크롤링 데이터 병합 완료")
except Exception as e:
    print(f"❌ 크롤링 데이터 병합 실패: {e}")

# ====================
# 3️⃣ KoBERT 임베딩 생성
# ====================
tokenizer = AutoTokenizer.from_pretrained("monologg/kobert", trust_remote_code=True)
bert_model = AutoModel.from_pretrained("monologg/kobert", trust_remote_code=True)

def get_bert_embedding(texts):
    embeddings = []
    for text in tqdm(texts, desc="임베딩 중"):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
        with torch.no_grad():
            outputs = bert_model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        embeddings.append(cls_embedding)
    return np.array(embeddings)

# ====================
# 4️⃣ 예측
# ====================
try:
    df["제출주체"] = df["청원제목"].apply(lambda x: 1 if "법안" in str(x) else 0)
    texts = (df["청원제목"].fillna('') + " " + df["청원내용"].fillna('')).tolist()
    embeddings = get_bert_embedding(texts)
    features = np.hstack((embeddings, df[["제출주체"]].values))

    scaled_preds = model.predict(features)
    pred_scores = scaler.inverse_transform(scaled_preds.reshape(-1, 1)).flatten()
    df["승인 확률"] = np.round(pred_scores, 2)

    df[["청원제목", "승인 확률"]].to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 예측 결과 저장 완료 → {output_path}")
except Exception as e:
    print(f"❌ 예측 실패: {e}")


