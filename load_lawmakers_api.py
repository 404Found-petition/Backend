import requests
import ast
import os
import django
import re
import csv
from collections import defaultdict

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "petition.settings")
django.setup()

from lawmembers.models import Lawmaker, Bill

API_KEY = "DEMO-KEY"  # 실제 실행 시 발급받은 키로 변경
AGE = 21
PAGE_SIZE = 100

FIELD_KEYWORDS = {
    "정치·행정": ["정부", "행정", "정책", "의회", "지자체", "법안", "입법"],
    "사회": ["복지", "인권", "범죄", "노동", "주거", "청년", "아동", "노인", "여성", "장애"],
    "경제·산업": ["금융", "세금", "산업", "소상공인", "무역", "경제", "투자"],
    "교육": ["학교", "교사", "학생", "교육", "입시", "학제", "교과", "학습"],
    "환경": ["기후", "환경", "탄소", "미세먼지", "에코", "온난화", "생태", "녹지"],
    "교통·건설": ["도로", "지하철", "철도", "공항", "건설", "교통", "시설"],
    "보건·의료": ["병원", "의료", "복지", "건강", "치료", "백신", "감염병"],
    "문화·예술": ["영화", "공연", "예술", "문화", "전통", "관광", "콘텐츠"],
    "과학·기술": ["AI", "인공지능", "로봇", "반도체", "기술", "과학", "연구"],
    "국방·외교": ["군", "안보", "국방", "외교", "통일", "북한", "안전보장"]
}

def determine_field(texts):
    score = defaultdict(int)
    for text in texts:
        for field, keywords in FIELD_KEYWORDS.items():
            for keyword in keywords:
                score[field] += len(re.findall(rf"\\b{re.escape(keyword)}\\b", text))
    return max(score.items(), key=lambda x: x[1])[0] if score else "정치·행정"

def fetch_lawmakers():
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    result = {}
    for page in range(1, 10):
        params = {"KEY": API_KEY, "Type": "json", "pIndex": page, "pSize": PAGE_SIZE}
        r = requests.get(url, params=params).json()
        pttrcp = r.get('PTTRCP', [])
        if len(pttrcp) < 2 or 'row' not in pttrcp[1]:
            break
        for row in pttrcp[1]['row']:
            name = row['INTD_ASBLM_NM'].split()[0].replace("의원", "")
            party = row.get('POLY_NM', '미상')
            result[name] = {"name": name, "party": party, "bills": [], "petitions": []}
    return result

def fetch_bills(lawmakers):
    url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
    for page in range(1, 10):
        params = {"KEY": API_KEY, "Type": "json", "pIndex": page, "pSize": PAGE_SIZE, "AGE": AGE}
        r = requests.get(url, params=params).json()
        bills_data = r.get('nzmimeepazxkubdpn', [])
        if len(bills_data) < 2 or 'row' not in bills_data[1]:
            break
        for row in bills_data[1]['row']:
            proposer = row.get("RST_PROPOSER", "").replace("의원", "").split(',')[0].strip()
            title = row.get("BILL_NAME", "")
            if proposer in lawmakers:
                lawmakers[proposer]['bills'].append(title)

def fetch_petitions(lawmakers):
    url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    for page in range(1, 10):
        params = {"KEY": API_KEY, "Type": "json", "pIndex": page, "pSize": PAGE_SIZE}
        r = requests.get(url, params=params).json()
        pttrcp = r.get('PTTRCP', [])
        if len(pttrcp) < 2 or 'row' not in pttrcp[1]:
            break
        for row in pttrcp[1]['row']:
            names = row.get("INTD_ASBLM_NM", "").replace("의원", "").split(',')
            title = row.get("PTT_NM", "")
            for name in names:
                name = name.strip().split()[0]
                if name in lawmakers:
                    lawmakers[name]['petitions'].append(title)

# API 데이터 수집
lawmakers = fetch_lawmakers()
fetch_bills(lawmakers)
fetch_petitions(lawmakers)

# CSV 저장
with open('api_lawmaker_data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["이름", "정당", "대표분야", "법률안목록", "청원목록"])
    for i, (name, data) in enumerate(lawmakers.items(), start=1):
        texts = data['bills'] + data['petitions']
        rep_field = determine_field(texts)
        bills_joined = "; ".join(data['bills'])
        petitions_joined = "; ".join(data['petitions'])
        writer.writerow([name, data['party'], rep_field, bills_joined, petitions_joined])

# CSV 파일로부터 DB 삽입
with open('api_lawmaker_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        lawmaker, _ = Lawmaker.objects.get_or_create(
            name=row['이름'],
            defaults={"seat_number": i, "party": row['정당'], "representative_field": row['대표분야']}
        )
        lawmaker.representative_field = row['대표분야']
        lawmaker.party = row['정당']
        lawmaker.seat_number = i
        lawmaker.save()

        for title in row['법률안목록'].split('; '):
            if title:
                Bill.objects.get_or_create(lawmaker=lawmaker, title=title)
