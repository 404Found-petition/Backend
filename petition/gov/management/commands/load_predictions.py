'''
청원 동의 현황 업데이트 할 때마다 터미널에 입력(DB 저장 코드)
python manage.py load_predictions
'''
iimport os
import pandas as pd
from django.core.management.base import BaseCommand
from petition.gov.models import PredictionResult
from django.conf import settings

class Command(BaseCommand):
    help = '예측결과 CSV 파일을 로드하여 PredictionResult 모델에 저장합니다.'

    def handle(self, *args, **kwargs):
        # CSV 파일 경로 설정
        csv_path = os.path.join(settings.BASE_DIR, 'AI', '예측결과.csv')

        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV 파일이 존재하지 않습니다: {csv_path}")
            
            # CSV 파일 읽기
            df = pd.read_csv(csv_path)

            # 필수 컬럼이 없는 경우 예외 처리
            required_columns = ['청원제목', '청원내용', '승인 확률']
            for column in required_columns:
                if column not in df.columns:
                    raise ValueError(f"CSV 파일에 '{column}' 컬럼이 없습니다.")

            # 예측 결과 저장
            for _, row in df.iterrows():
                # 데이터 유효성 체크: 빈 값이 있으면 건너뜁니다.
                if not row["청원제목"] or pd.isna(row["승인 확률"]):
                    self.stdout.write(self.style.WARNING(f"경고: 빈 값이 있어 '{row['청원제목']}'는 저장되지 않았습니다."))
                    continue  # 빈 값이 있으면 건너뜁니다.

                try:
                    PredictionResult.objects.create(
                        petition_title=row["청원제목"],
                        petition_content=row.get("청원내용", ""),  # 청원내용이 없을 수 있기 때문에 기본값 설정
                        prediction_percentage=row["승인 확률"]
                    )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"예측 결과 저장 실패: {row['청원제목']} -> {e}"))
                    continue

            self.stdout.write(self.style.SUCCESS('✅ 예측 결과가 성공적으로 저장되었습니다.'))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'❌ 파일 오류: {e}'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'❌ CSV 포맷 오류: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 예기치 않은 오류 발생: {e}'))
