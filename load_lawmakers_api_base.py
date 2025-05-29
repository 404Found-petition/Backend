from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.http import HttpResponse
import requests
import csv
import io

# 백엔드입력용_의원정보통합_정당정정본.csv 파일의 베이스가 되는 CSV 파일 생성용 코드~

# 1. /api/lawmaker-info/ - 이름, 정당만 응답
class LawmakerAPIProxyView(APIView):
    def get(self, request):
        try:
            api_key = settings.OPENCONGRESS_KEY
            url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
            res = requests.get(url, params={"KEY": api_key, "Type": "json", "pIndex": 1, "pSize": 1000})
            res.raise_for_status()

            data = res.json()
            lawmakers = data["nwvrqwxyaytdsfvhu"][1]["row"]

            simplified = [
                {"이름": lw["HG_NM"], "소속정당": lw["POLY_NM"]}
                for lw in lawmakers
            ]

            return Response(simplified)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# 2. /api/lawmaker-detail/?name=홍길동 - 법률안/청원 포함
class LawmakerDetailAPIView(APIView):
    def get(self, request):
        name = request.query_params.get("name")
        if not name:
            return Response({"error": "name 파라미터가 필요합니다."}, status=400)

        try:
            api_key = settings.OPENCONGRESS_KEY

            # 발의 법률안 요청
            bills_url = "https://open.assembly.go.kr/portal/openapi/ncryefyuaflxnqbqo"
            bills_res = requests.get(bills_url, params={"KEY": api_key, "Type": "json", "pIndex": 1, "pSize": 100, "MEM_NAME": name})
            bills = bills_res.json().get("ncryefyuaflxnqbqo", [None, {"row": []}])[1]["row"]
            bill_names = [b["BILL_NAME"] for b in bills[:3]]

            # 청원 요청
            petitions_url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
            petitions_res = requests.get(petitions_url, params={"KEY": api_key, "Type": "json", "pIndex": 1, "pSize": 100, "PETI_MEM_NM": name})
            petitions = petitions_res.json().get("nzmimeepazxkubdpn", [None, {"row": []}])[1]["row"]
            petition_summaries = [p["PETI_DESC"][:30] + "..." for p in petitions[:2]]

            return Response({
                "이름": name,
                "발의 법률안": bill_names,
                "청원": petition_summaries
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)

# 3. /api/lawmaker-csv/ - 전체 데이터 CSV 리턴
class LawmakerCSVAPIView(APIView):
    def get(self, request):
        try:
            api_key = settings.OPENCONGRESS_KEY
            lawmakers_url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
            res = requests.get(lawmakers_url, params={"KEY": api_key, "Type": "json", "pIndex": 1, "pSize": 1000})
            lawmakers = res.json()["nwvrqwxyaytdsfvhu"][1]["row"]

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["이름", "소속정당", "발의 법률/청원"])

            for lw in lawmakers:
                name = lw.get("HG_NM", "")
                party = lw.get("POLY_NM", "")

                # 법률안
                bills_res = requests.get(
                    "https://open.assembly.go.kr/portal/openapi/ncryefyuaflxnqbqo",
                    params={"KEY": api_key, "Type": "json", "pIndex": 1, "pSize": 100, "MEM_NAME": name})
                bills = bills_res.json().get("ncryefyuaflxnqbqo", [None, {"row": []}])[1]["row"]
                bill_names = [b["BILL_NAME"] for b in bills[:2]]

                # 청원
                petitions_res = requests.get(
                    "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn",
                    params={"KEY": api_key, "Type": "json", "pIndex": 1, "pSize": 100, "PETI_MEM_NM": name})
                petitions = petitions_res.json().get("nzmimeepazxkubdpn", [None, {"row": []}])[1]["row"]
                petition_summaries = [p["PETI_DESC"][:30] + "..." for p in petitions[:1]]

                merged = "; ".join(bill_names + petition_summaries)
                writer.writerow([name, party, merged])

            output.seek(0)
            response = HttpResponse(output, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="의원정보_베이스.csv"'
            return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)
