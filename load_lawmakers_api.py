import os
import django
import csv
import ast  # 🔸 추가

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petition.settings")
django.setup()

from lawmembers.models import Lawmaker, Bill
from django.db import models

csv_path = os.path.join(os.path.dirname(__file__), "백엔드입력용_의원정보통합_정당정정본.csv")

with open(csv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for raw_row in reader:
        row = {key.strip(): value.strip() for key, value in raw_row.items()}

        try:
            if not row["좌석번호"].isdigit():
                print(f"⚠️ 좌석번호 비어있음 (의원: {row.get('이름', '미상')}) → 건너뜀")
                continue

            seat_number = int(row["좌석번호"])
            name = row["이름"]
            party = row["정당"]
            rep_field = row.get("대표분야", "정치·행정")
            bill_titles_raw = row.get("법률안목록", "")

            lawmaker = Lawmaker.objects.filter(
                models.Q(name=name) | models.Q(seat_number=seat_number)
            ).first()

            if not lawmaker:
                lawmaker = Lawmaker(
                    name=name,
                    seat_number=seat_number,
                    party=party,
                    representative_field=rep_field,
                )
            else:
                lawmaker.name = name
                lawmaker.seat_number = seat_number
                lawmaker.party = party
                lawmaker.representative_field = rep_field

            lawmaker.save()

            if bill_titles_raw:
                try:
                    bill_list = ast.literal_eval(bill_titles_raw)
                except Exception as e:
                    print(f"❌ 법률안목록 파싱 실패 (의원: {name}): {e}")
                    bill_list = []

                for title in bill_list:
                    if title:
                        Bill.objects.get_or_create(lawmaker=lawmaker, title=title)

        except Exception as e:
            print(f"❌ 오류 발생 (의원: {row.get('이름', '미상')}): {e}")

print("✅ 모든 의원 정보가 성공적으로 저장되었습니다.")
