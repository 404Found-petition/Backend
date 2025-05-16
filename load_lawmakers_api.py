import os
import django
import csv

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petition.settings")
django.setup()

from lawmembers.models import Lawmaker, Bill

csv_path = os.path.join(os.path.dirname(__file__), "백엔드입력용_의원정보통합_정당정정본.csv")

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        lawmaker, created = Lawmaker.objects.get_or_create(
            name=row["이름"],
            defaults={
                "seat_number": i,
                "party": row["정당"],
                "representative_field": row.get("대표분야", "정치·행정"),
            }
        )
        # 기존 데이터 덮어쓰기
        lawmaker.seat_number = i
        lawmaker.party = row["정당"]
        lawmaker.representative_field = row.get("대표분야", "정치·행정")
        lawmaker.save()

        # 법률안목록이 있을 경우 Bill 모델에 저장
        if "법률안목록" in row and row["법률안목록"]:
            titles = row["법률안목록"].split("; ")
            for title in titles:
                if title:
                    Bill.objects.get_or_create(lawmaker=lawmaker, title=title)
