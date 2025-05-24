# ai/load_predictions.py

import os
import csv
import sys
import django

# ✅ 현재 스크립트의 상위 폴더(= backend/)를 모듈 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# ✅ settings 모듈 등록
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petition.settings")
django.setup()


# ✅ Django 환경 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petition.settings")
django.setup()

from ai.models import CsvPrediction

file_path = os.path.join("ai", "예측결과.csv")

count = 0
with open(file_path, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        CsvPrediction.objects.create(
            title=row["청원제목"].strip(),
            summary=row["청원내용"].strip(),
            probability=float(row["승인 확률"])
        )
        count += 1

print(f"✅ 예측결과 {count}건 CsvPrediction에 저장 완료")
