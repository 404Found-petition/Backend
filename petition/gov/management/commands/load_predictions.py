'''
청원 동의 현황 업데이트 할 때마다 터미널에 입력(DB 저장 코드)
python manage.py load_predictions
'''
import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from petition.gov.models import PredictionResult
from petition.utils.csv_utils import save_prediction_to_csv, export_predictions_to_csv

class Command(BaseCommand):
    help = '예측결과 CSV 파일을 로드하여 PredictionResult 모델에 저장합니다.'

    def handle(self, *args, **kwargs):
        csv_path = os.path.join(settings.BASE_DIR, 'AI', '예측결과.csv')

        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV 파일이 존재하지 않습니다: {csv_path}")
            
            df = pd.read_csv(csv_path)

            required_columns = ['청원제목', '청원내용', '승인 확률']
            for column in required_columns:
                if column not in df.columns:
                    raise ValueError(f"CSV 파일에 '{column}' 컬럼이 없습니다.")

            saved_rows = []
            for _, row in df.iterrows():
                if not row["청원제목"] or pd.isna(row["승인 확률"]):
                    self.stdout.write(self.style.WARNING(f"빈 값이 있어 '{row['청원제목']}'는 저장되지 않았습니다."))
                    continue

                try:
                    PredictionResult.objects.create(
                        petition_title=row["청원제목"],
                        petition_content=row.get("청원내용", ""),
                        prediction_percentage=row["승인 확률"]
                    )
                    saved_rows.append({
                        "청원제목": row["청원제목"],
                        "청원내용": row.get("청원내용", ""),
                        "승인 확률": row["승인 확률"]
                    })
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"예측 결과 저장 실패: {row['청원제목']} -> {e}"))
                    continue

            # ✅ [8] 예측된 행들을 다시 예측결과.csv로 저장
            save_prediction_to_csv(saved_rows)

            # ✅ [5] DB 전체 PredictionResult를 백업 CSV로 저장
            export_predictions_to_csv('db_exported_predictions.csv')

            self.stdout.write(self.style.SUCCESS('✅ 예측 결과 저장 완료 및 CSV 백업 완료'))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'❌ 파일 오류: {e}'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'❌ CSV 포맷 오류: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 예기치 않은 오류 발생: {e}'))