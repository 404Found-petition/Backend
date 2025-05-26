# backend/ai/bert_utils.py
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

# KoBERT 로드
tokenizer = AutoTokenizer.from_pretrained("monologg/kobert")
model_bert = AutoModel.from_pretrained("monologg/kobert")

def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
    with torch.no_grad():
        outputs = model_bert(**inputs)
    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
    return cls_embedding
