from django.core.management.base import BaseCommand
from keywordAnalysis.crawl_petition import main

# 국회 API를 통해 제13대~22대 청원 데이터를 수집하고,
# 요약 정보를 포함한 CSV 파일('병합된_청원_데이터.csv')로 저장하는 스크립트.

# - 외부 API 호출 → JSON 데이터 수집
# - 각 청원의 상세 페이지를 크롤링하여 요약 추출
# - Pandas를 사용해 정리하고 CSV로 저장

# Django management command로 등록되어 있으므로
# python manage.py update_petitions 으로 실행 가능.

# crontab 등에 등록하면 월 1회 자동 실행도 가능합니다.

class Command(BaseCommand):
    help = "국회 API에서 청원 데이터를 수집해 CSV로 저장합니다."

    def handle(self, *args, **kwargs):
        main()
        self.stdout.write(self.style.SUCCESS("청원 데이터 업데이트 완료"))
