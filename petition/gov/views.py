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
from .models import CustomUser, History, PredictionResult, Post, Vote, Comment
from .serializers import CustomUserSerializer, LoginSerializer, HistorySerializer, PredictionResultSerializer, UserUpdateSerializer, PostSerializer
from wcdata.utils import extract_keywords_by_month, get_available_months
from keywordAnalysis.fieldValue import get_field_counts
from django.core.paginator import Paginator
from django.shortcuts import redirect


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
        user = request.user

        # 사용자가 작성한 게시글, 댓글, 예측 기록 등 삭제
        user.posts.all().delete()  # 사용자가 작성한 게시글 삭제
        user.comments.all().delete()  # 사용자가 작성한 댓글 삭제
        user.history.all().delete()  # 사용자가 작성한 예측 기록 삭제
        user.delete()  # 사용자 삭제

        return Response({
            "success": True,
            "message": "회원 탈퇴 완료, 모든 정보와 콘텐츠가 삭제되었습니다."
        })

# 로그인 뷰
class LoginView(APIView):
    def post(self, request):
        # LoginSerializer를 사용하여 로그인 시도
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            # 로그인 후 메인 화면으로 리다이렉트
            return redirect('home')  # 'home'은 메인 페이지의 URL 패턴명입니다.

        # 로그인 실패 시 오류 메시지 반환
        return Response({
            "success": False,
            "message": "아이디나 비밀번호가 올바르지 않습니다."
        }, status=status.HTTP_400_BAD_REQUEST)

#로그아웃 뷰
class LogoutView(APIView):
    def post(self, request):
        # 로그아웃 요청 처리
        user = request.user
        session_token = request.auth_token  # 사용자의 인증 토큰

        # 토큰 삭제
        request.user.auth_token.delete()

        # 로그아웃 이벤트 기록 (예: 로그아웃 시간, 성공 여부)
        logout_event = LogoutEvent(
            user_id=user.id,
            logout_time=datetime.now(),
            successful=True  # 로그아웃이 성공적으로 처리됨
        )
        logout_event.save()  # 이벤트 저장 (로그 기록 등)

        # 응답 반환
        return Response({
            "status": "success",
            "message": "로그아웃 완료",
            "session_token_removed": True  # 세션 토큰이 삭제되었음을 응답
        }, status=status.HTTP_200_OK)
        
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

# 회원 정보 수정 뷰
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "회원 정보 수정 완료"
            }, status=200)
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)

# 게시글 페이지네이션 뷰
class PostPaginationView(APIView):
    def get(self, request):
        page = request.query_params.get("page", 1)
        posts = Post.objects.all().order_by('-created_at')
        paginator = Paginator(posts, 4)

        try:
            paginated = paginator.page(page)
        except:
            return Response({
                "success": False,
                "message": "존재하지 않는 페이지입니다."
            }, status=404)

        serializer = PostSerializer(paginated, many=True)
        return Response({
            "success": True,
            "message": "게시글 조회 성공",
            "data": serializer.data,
            "page": int(page),
            "total_pages": paginator.num_pages
        })

# 청원 예측을 수행하고 결과를 기록하는 API
class PetitionPredictView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 예측 가능

    def post(self, request):
        petition_text = request.data.get('petition_text')
        user = request.user

        if not petition_text:
            return Response({"error": "청원 내용을 입력해주세요."}, status=400)

        try:
            model = joblib.load(BASE_DIR / 'AI' / '청원_예측모델.pkl')
            scaler = joblib.load(BASE_DIR / 'AI' / 'scaler.pkl')

            embedding = get_bert_embedding(petition_text)
            is_law = 1 if "법안" in petition_text else 0
            features = np.hstack((embedding, is_law)).reshape(1, -1)

            pred_scaled = model.predict(features)
            pred_score = scaler.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]

        except Exception as e:
            return Response({"error": "AI 예측 중 오류 발생"}, status=500)

        # 예측 결과를 History 모델에 저장
        history = History.objects.create(
            user=user,
            search_petition=petition_text,
            search_petition_percentage=pred_score
        )

        return Response({
            "success": True,
            "predicted_percentage": round(pred_score, 2),
            "history_id": history.id
        }, status=200)

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

# 개인이 과거에 청원 예측 수행한 결과 기록 조회 API
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

# 로그인한 사용자가 예측 결과를 조회하는 API  --> 모든 사람이 다 볼 수 있게 변경
class PredictionResultView(APIView):
    def get(self, request):
        results = PredictionResult.objects.all().order_by('-predicted_at')
        serializer = PredictionResultSerializer(results, many=True)
        return Response({
            "success": True,
            "message": "예측 결과 조회 성공",
            "data": serializer.data
        }, status=200)
    
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
        
# 게시글 작성 API
class PostCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        title = request.data.get('title')
        content = request.data.get('content')
        has_poll = request.data.get('has_poll', False)

        if not title or not content:
            return Response({"error": "제목과 내용을 입력해야 합니다."}, status=400)

        post = Post.objects.create(
            user=request.user,
            title=title,
            content=content,
            has_poll=has_poll
        )

        return Response({"success": True, "message": "게시글 작성 완료", "post": PostSerializer(post).data}, status=201)

# 찬반 투표 API
class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')
        choice = request.data.get('choice')  # 'yes' or 'no'
        user = request.user

        try:
            post = Post.objects.get(id=post_id)
            if not post.has_poll:
                return Response({"error": "이 게시글에는 투표 기능이 없습니다."}, status=400)
        except Post.DoesNotExist:
            return Response({"error": "게시글을 찾을 수 없습니다."}, status=404)

        vote, created = Vote.objects.update_or_create(
            post=post, user=user,
            defaults={"choice": choice == 'yes'}
        )

        return Response({"success": True, "message": "투표 완료"}, status=200)

# 댓글 작성 API
class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        content = request.data.get('content')

        if not content:
            return Response({"error": "댓글 내용을 입력해야 합니다."}, status=400)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "게시글을 찾을 수 없습니다."}, status=404)