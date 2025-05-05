'''
청원 동의 현황 업데이트 할 때마다 터미널에 입력(DB 저장 코드)
python manage.py load_predictions
'''
import os
import pandas as pd
from django.core.management.base import BaseCommand
from petition.gov.models import PredictionResult  # 올바른 모델 임포트
from django.conf import settings

class Command(BaseCommand):
    help = '예측결과 CSV 파일을 로드하여 PredictionResult 모델에 저장합니다.'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(settings.BASE_DIR, 'AI', '예측결과.csv')

        try:
            # 예측결과.csv 파일 읽기
            df = pd.read_csv(csv_path)
            
            # PredictionResult 모델에 데이터 저장
            for _, row in df.iterrows():
                PredictionResult.objects.create(
                    petition_title=row["청원제목"],
                    prediction_percentage=row["승인 확률"]
                )
            
            self.stdout.write(self.style.SUCCESS('✅ 예측 결과가 성공적으로 저장되었습니다.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 오류 발생: {e}'))

