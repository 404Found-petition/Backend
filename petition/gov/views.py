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
from .models import CustomUser, History, PredictionResult
from .serializers import CustomUserSerializer, LoginSerializer, HistorySerializer, PredictionResultSerializer
from wcdata.utils import extract_keywords_by_month, get_available_months
from keywordAnalysis.fieldValue import get_field_counts

# KoBERT 모델 초기화
tokenizer = AutoTokenizer.from_pretrained("monologg/kobert", trust_remote_code=True)
bert_model = AutoModel.from_pretrained("monologg/kobert", trust_remote_code=True)

# BERT 임베딩 추출 함수
def get_bert_embedding(text):
    # 입력 텍스트를 BERT 모델에 입력하기 위한 텐서 형식으로 변환
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding="max_length", max_length=128)
    # BERT 모델을 통해 임베딩을 추출
    with torch.no_grad():
        outputs = bert_model(**inputs)
    # [CLS] 토큰의 임베딩을 가져오고, 이를 numpy 배열로 반환
    cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
    return cls_embedding

# 회원가입 뷰
class RegisterView(APIView):
    def post(self, request):
        # 전달된 데이터를 CustomUserSerializer로 검증
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            # 데이터가 유효하면 사용자 생성 후 저장
            serializer.save()  
            return Response({
                "success": True,
                "message": "회원가입이 완료되었습니다."
            }, status=status.HTTP_201_CREATED)
        # 데이터 검증 실패 시 오류 메시지 반환
        return Response({
            "success": False,
            "message": "입력값을 확인해주세요.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 회원 탈퇴 뷰
class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        # 로그인된 사용자의 정보를 삭제
        request.user.delete()
        return Response({
            "success": True,
            "message": "회원 탈퇴 완료, 로그아웃 되었습니다."
        })

# 로그인 뷰
class LoginView(APIView):
    def post(self, request):
        # LoginSerializer를 사용하여 로그인 시도
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            # 인증 성공 시 access token과 refresh token 반환
            return Response({
                "success": True,
                "message": "로그인 성공",
                "access": str(refresh.access_token),
                "refresh": str(refresh)  
            }, status=status.HTTP_200_OK)
        # 로그인 실패 시 오류 메시지 반환
        return Response({
            "success": False,
            "message": "아이디나 비밀번호가 올바르지 않습니다."
        }, status=status.HTTP_400_BAD_REQUEST)

# 아이디, 닉네임 중복 체크 API
@api_view(['GET'])
def check_duplicate(request):
    # 쿼리 파라미터로 아이디와 닉네임 값을 받아옴
    userid = request.query_params.get('userid')
    nickname = request.query_params.get('nickname')

    # 아이디 중복 여부 확인
    if userid and CustomUser.objects.filter(userid=userid).exists():
        return Response({"success": False, "field": "userid", "message": "이미 사용 중인 아이디입니다."})
    
    # 닉네임 중복 여부 확인
    if nickname and CustomUser.objects.filter(nickname=nickname).exists():
        return Response({'field': 'nickname', 'available': False})

    return Response({"success": True, "message": "사용 가능한 아이디입니다."})

# 청원 예측을 수행하고 결과를 기록하는 API
class PetitionPredictView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        petition_text = request.data.get('petition_text')
        user = request.user  # 로그인한 사용자 정보

        # 청원 내용이 없을 경우 오류 반환
        if not petition_text:
            return Response({"error": "청원 내용을 입력해주세요."}, status=400)

        try:
            # 예측 모델과 스케일러 불러오기
            BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
            model = joblib.load(BASE_DIR / 'AI' / '청원_예측모델.pkl')
            scaler = joblib.load(BASE_DIR / 'AI' / 'scaler.pkl')

            # BERT 임베딩과 법안 여부 특징을 결합한 피처 생성
            embedding = get_bert_embedding(petition_text)
            is_law = 1 if "법안" in petition_text else 0
            features = np.hstack((embedding, is_law)).reshape(1, -1)

            # 예측 수행
            pred_scaled = model.predict(features)
            pred_score = scaler.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]

        except Exception as e:
            print("❌ 모델 예측 실패:", e)
            return Response({
                "success": False,
                "message": "AI 예측 중 오류 발생"
            }, status=500)

        # 예측 결과를 History에 기록
        history = History.objects.create(
            user=user,
            search_petition=petition_text,
            search_petition_percentage=pred_score
        )

        return Response({
            "success": True,
            "message": "예측 완료",
            "predicted_percentage": round(pred_score, 2),
            "history_id": history.id
        }, status=200)

# 예측 기록 조회 API
class MyHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        history = History.objects.filter(user=user).order_by('-history_date')
        serializer = HistorySerializer(history, many=True)
        return Response({
            "success": True,
            "message": "예측 기록 조회 성공",
            "data": serializer.data
        })

# 워드클라우드 관련 데이터 조회 API
@api_view(['GET'])
def wordcloud_data(request):
    # month 파라미터 받아오기
    month = request.query_params.get("month")
    if not month:
        return Response({"error": "month 쿼리 파라미터가 필요합니다."}, status=400)

    try:
        # 월별 키워드 추출 함수 호출
        keywords = extract_keywords_by_month(month)
        return Response({
            "success": True,
            "message": "분야 통계 조회 성공",
            "data": keywords
        }, status=200)
    except Exception as e:
        print("❌ 워드클라우드 데이터 추출 실패:", e)
        return Response({
            "success": False,
            "message": "서버 내부 오류"
        }, status=500)

# 워드클라우드 관련 월별 데이터 조회 API
@api_view(['GET'])
def wordcloud_months(request):
    try:
        # 사용 가능한 월 목록 가져오기
        months = get_available_months()
        return Response({
            "success": True,
            "message": "월 목록 조회 성공",
            "data": months
        }, status=200)
    except Exception as e:
        print("❌ 월 목록 가져오기 실패:", e)
        return Response({
            "success": False,
            "message": "서버 내부 오류"
        }, status=500)

# TF-IDF 방식의 워드클라우드 데이터 조회 API
@api_view(['GET'])
def wordcloud_data_tfidf(request):
    # month 파라미터 받아오기
    month = request.query_params.get("month")
    if not month:
        return Response({"success": False, 
            "message": "month 쿼리 파라미터가 필요합니다."
            }, status=400)
    try:
        # TF-IDF 방식으로 키워드 추출
        keywords = extract_keywords_by_month_tfidf(month)
        return Response({"success": True, 
            "data": keywords
            }, status=200)
    except Exception as e:
        print("❌ TF-IDF 데이터 추출 실패:", e)
        return Response({"success": False, 
            "message": "분석 중 오류 발생"
            }, status=500)

# 청원 분야 통계 조회 API
@api_view(['GET'])
def petition_field_stats(request):
    try:
        # 분야 통계 추출
        result = get_field_counts()
        return Response({
            "success": True,
            "message": "분야 통계 조회 성공",
            "data": result
        }, status=200)
    except Exception as e:
        print("❌ 분야 통계 처리 실패:", e)
        return Response({
            "success": False,
            "message": "서버 내부 오류"
        }, status=500)

# 로그인한 사용자가 예측 결과를 조회하는 API
class PredictionResultView(APIView):
    def get(self, request):
        user = request.user
        # 예측 결과 조회 (최신 10개만)
        results = PredictionResult.objects.filter(user=user).order_by('-predicted_at')[:10]
        serializer = PredictionResultSerializer(results, many=True)
        return Response(serializer.data)

# 모든 사용자가 조회할 수 있는 게시글 목록 API
class PetitionListView(APIView):
    def get(self, request):
        # 모든 청원 데이터를 조회
        petitions = Petition.objects.all()  
        serializer = PetitionSerializer(petitions, many=True)
        return Response({
            "success": True,
            "message": "청원 리스트 조회 성공",
            "data": serializer.data
        }, status=200)
        
# 투표 기능 API
class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')
        choice = request.data.get('choice')  # 'yes' or 'no'
        user = request.user

        # 유효한 선택지 확인
        if choice not in ['yes', 'no']:
            return Response(
                {"success": False, "message": "선택지는 'yes' 또는 'no'만 가능합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response(
                {"success": False, "message": "해당 게시글이 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 투표 결과 업데이트 (존재하지 않으면 새로 생성)
        vote, created = Vote.objects.update_or_create(
            post=post, user=user,
            defaults={"choice": choice}
        )

        return Response(
            {
                "success": True,
                "message": "투표가 완료되었습니다.",
                "updated": not created
            },
            status=status.HTTP_200_OK
        )

