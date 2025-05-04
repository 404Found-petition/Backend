from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import os
import pathlib
import joblib
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from .models import CustomUser, History
from .serializers import CustomUserSerializer, LoginSerializer, HistorySerializer
from wcdata.utils import extract_keywords_by_month, get_available_months
from keywordAnalysis.fieldValue import get_field_counts

# KoBERT 초기화
tokenizer = AutoTokenizer.from_pretrained("monologg/kobert", trust_remote_code=True)
bert_model = AutoModel.from_pretrained("monologg/kobert", trust_remote_code=True)

def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
    return cls_embedding

class RegisterView(APIView):
    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "회원가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': '로그인 성공'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def check_duplicate(request):
    userid = request.query_params.get('userid')
    nickname = request.query_params.get('nickname')

    if userid and CustomUser.objects.filter(userid=userid).exists():
        return Response({'field': 'userid', 'available': False})
    if nickname and CustomUser.objects.filter(nickname=nickname).exists():
        return Response({'field': 'nickname', 'available': False})

    return Response({'available': True})

class PetitionPredictView(APIView):
    def post(self, request):
        petition_text = request.data.get('petition_text')
        user_id = request.data.get('user_id')

        if not petition_text or not user_id:
            return Response({"error": "청원 내용과 유저 ID를 모두 입력해주세요."}, status=400)

        try:
            BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
            model = joblib.load(BASE_DIR / 'AI' / '청원_예측모델.pkl')
            scaler = joblib.load(BASE_DIR / 'AI' / 'scaler.pkl')

            embedding = get_bert_embedding(petition_text)
            is_law = 1 if "법안" in petition_text else 0
            features = np.hstack((embedding, is_law)).reshape(1, -1)

            pred_scaled = model.predict(features)
            pred_score = scaler.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]

        except Exception as e:
            print("❌ 모델 예측 실패:", e)
            return Response({"error": "AI 예측 중 오류 발생"}, status=500)

        history = History.objects.create(
            user_id=user_id,
            search_petition=petition_text,
            search_petition_percentage=pred_score
        )

        return Response({
            "predicted_percentage": round(pred_score, 2),
            "history_id": history.id
        }, status=200)

class MyHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        history = History.objects.filter(user=user).order_by('-history_date')
        serializer = HistorySerializer(history, many=True)
        return Response(serializer.data)

# ✅ 워드클라우드 관련 API
@api_view(['GET'])
def wordcloud_data(request):
    month = request.query_params.get("month")
    if not month:
        return Response({"error": "month 쿼리 파라미터가 필요합니다."}, status=400)

    try:
        keywords = extract_keywords_by_month(month)
        return Response(keywords, status=200)
    except Exception as e:
        print("❌ 워드클라우드 데이터 추출 실패:", e)
        return Response({"error": "분석 중 오류 발생"}, status=500)

@api_view(['GET'])
def wordcloud_data_tfidf(request):
    return wordcloud_data(request)

@api_view(['GET'])
def wordcloud_months(request):
    try:
        months = get_available_months()
        return Response(months, status=200)
    except Exception as e:
        print("❌ 월 목록 가져오기 실패:", e)
        return Response({"error": "월 목록 조회 중 오류 발생"}, status=500)
    
@api_view(['GET'])
def petition_field_stats(request):
    try:
        result = get_field_counts()
        return Response(result, status=200)
    except Exception as e:
        print("❌ 분야 통계 처리 실패:", e)
        return Response({"error": "서버 내부 오류"}, status=500)
