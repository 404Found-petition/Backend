import pandas as pd
import ast
from lawmembers.models import Lawmaker, Bill

# CSV 파일 경로
csv_path = "백엔드입력용_의원정보통합_정당정정본.csv"

# 파일 읽기
df = pd.read_csv(csv_path)

# 문자열 리스트 → 실제 리스트로 변환
def parse_bills(raw):
    try:
        return ast.literal_eval(raw)
    except:
        return []

df['법률안목록'] = df['법률안목록'].apply(parse_bills)

# DB에 삽입
for i, row in df.iterrows():
    name = row['이름']
    party = row['정당'] if not pd.isna(row['정당']) else ''
    rep_field = row['대표분야']
    seat_number = i + 1  # 좌석번호 1~300 자동 배정

    # Lawmaker 생성 또는 업데이트
    lawmaker, _ = Lawmaker.objects.get_or_create(
        name=name,
        defaults={
            'party': party,
            'representative_field': rep_field,
            'seat_number': seat_number
        }
    )

    # 항상 정보 업데이트
    lawmaker.party = party
    lawmaker.representative_field = rep_field
    lawmaker.seat_number = seat_number
    lawmaker.save()

    # 최근 법률안 저장
    for title in row['법률안목록']:
        Bill.objects.get_or_create(lawmaker=lawmaker, title=title)
