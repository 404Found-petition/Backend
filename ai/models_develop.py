import pandas as pd
import pickle
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

# ✅ 파일 경로 설정
base_path = "/Users/sky/VSCode/petition/backend/AI"
csv_크롤링 = f"{base_path}/청원_처리_현황_크롤링완료.csv"
model_path = f"{base_path}/청원_예측모델.pkl"

# ✅ 데이터 불러오기
크롤링 = pd.read_csv(csv_크롤링, encoding='utf-8')

print(f"✔️ 크롤링된 청원 데이터 크기: {크롤링.shape[0]}")  # 확인을 위해 크기 출력

# ✅ 제출주체 컬럼 추가 (국민 vs. 국회의원)
크롤링["제출주체"] = 크롤링["청원제목"].apply(lambda x: 1 if "법안" in str(x) else 0)

# ✅ KoBERT 임베딩 함수 정의
tokenizer = AutoTokenizer.from_pretrained("monologg/kobert")
model_bert = AutoModel.from_pretrained("monologg/kobert")

def get_bert_embedding(texts):
    embeddings = []
    for text in tqdm(texts, desc="BERT 임베딩 생성"):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
        with torch.no_grad():
            outputs = model_bert(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        embeddings.append(cls_embedding)
    return np.array(embeddings)

# ✅ 모델 불러오기
with open(model_path, "rb") as f:
    model = pickle.load(f)

# ✅ 예측 수행
texts = (크롤링['청원제목'] + " " + 크롤링['청원내용']).astype(str).tolist()
embeddings = get_bert_embedding(texts)
X = np.hstack((embeddings, 크롤링[['제출주체']].values))

# ✅ 예측 결과 저장
크롤링['승인 확률'] = model.predict(X) * 100  # 확률을 백분율로 변환

# ✅ 예측 결과 파일로 저장
크롤링[['청원제목', '청원내용', '승인 확률']].to_csv(f"{base_path}/예측결과.csv", index=False, encoding='utf-8-sig')

print(f"✅ 예측 결과 저장 완료! 예측된 청원 수: {크롤링.shape[0]}")

