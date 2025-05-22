from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticatedOrReadOnly
import os
import pathlib
import joblib
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from .models import CustomUser, History, Post, Vote, Comment, Petition
from .serializers import CustomUserSerializer, LoginSerializer, HistorySerializer, PredictionResultSerializer, UserUpdateSerializer, PostSerializer, CommentSerializer, PetitionSerializer
from wcdata.utils import extract_keywords_by_month, get_available_months, extract_keywords_by_month_tfidf
from keywordAnalysis.csvutils import get_field_counts
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests
from .tokens import create_jwt_pair_for_user
from petition.gov.models import MonthlyKeyword, PredictionResult
from django.contrib.auth.hashers import make_password 
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication



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
        user = request.user  # 로그인된 사용자 정보

        try:
            # 사용자가 작성한 모든 게시글 삭제
            user.posts.all().delete()  # 이제 user.posts가 정상적으로 작동함
            user.comments.all().delete()
            user.history.all().delete()

            # 사용자 삭제
            user.delete()

            return Response({
                "success": True,
                "message": "회원 탈퇴 완료"
            }, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"오류 발생: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 로그인 뷰
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            return Response({
                "success": True,
                "message": "로그인 성공",
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": "아이디나 비밀번호가 올바르지 않습니다."
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # ✅ Refresh Token 무효화 (블랙리스트에 등록)

            return Response({
                "status": "success",
                "message": "로그아웃 완료"
            }, status=status.HTTP_205_RESET_CONTENT)

        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CustomUser  # 모델 import 필요

# 아이디 중복 체크 API
@api_view(['GET'])
def check_duplicate(request):
    # 쿼리 파라미터로 아이디 값을 받아옴
    userid = request.query_params.get('userid')
    print("📌 [중복 확인 요청] 받은 userid:", userid)

    # 아이디 중복 여부 확인
    if userid and CustomUser.objects.filter(userid=userid).exists():
        print("❌ [중복 확인 결과] 이미 존재하는 아이디입니다.")
        return Response({
            "success": False,
            "field": "userid",
            "message": "이미 사용 중인 아이디입니다.",
            "available": False
        })

    print("✅ [중복 확인 결과] 사용 가능한 아이디입니다.")
    return Response({
        "success": True,
        "message": "사용 가능한 아이디입니다.",
        "available": True
    })



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
            model = joblib.load(settings.BASE_DIR / 'AI' / '청원_예측모델.pkl')
            scaler = joblib.load(settings.BASE_DIR / 'AI' / 'scaler.pkl')

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

# 그래프
class PetitionStatisticsAPIView(APIView):
    def get(self, request):
        return Response(get_field_counts())

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

#청원 동의 현황 페이지 네이션     
class PetitionPaginationView(APIView):
    def get(self, request):
        page = request.query_params.get("page", 1)
        petitions = Petition.objects.all().order_by('-created_at')  # 최신순 정렬
        paginator = Paginator(petitions, 20)  # 한 페이지에 20개씩

        try:
            paginated = paginator.page(page)
        except:
            return Response({
                "success": False,
                "message": "존재하지 않는 페이지입니다."
            }, status=404)

        serializer = PetitionSerializer(paginated, many=True)
        return Response({
            "success": True,
            "message": "청원 조회 성공",
            "data": serializer.data,
            "page": int(page),
            "total_pages": paginator.num_pages
        })
        
# 게시글 작성 API (✅ 테스트용으로 인증 없이 허용)
class PostCreateView(APIView):
    # permission_classes = [IsAuthenticated]  # ← ✅ 테스트 시 주석 처리

    def post(self, request):
        title = request.data.get('title')
        content = request.data.get('content')
        has_poll = request.data.get('has_poll', False)

        if not title or not content:
            return Response({"error": "제목과 내용을 입력해야 합니다."}, status=400)

        # ✅ 로그인 안 해도 작성 가능하게 하기 위해 user=None 처리
        user = request.user if request.user.is_authenticated else None

        post = Post.objects.create(
            user=user,
            title=title,
            content=content,
            has_poll=has_poll
        )

        return Response({
            "success": True,
            "message": "게시글 작성 완료",
            "post": PostSerializer(post).data
        }, status=201)

# 단건 게시글 페이지 API
class PostDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
            post_data = PostSerializer(post).data

            comments = Comment.objects.filter(post=post).order_by('created_at')
            comment_data = CommentSerializer(comments, many=True).data

            yes_votes = Vote.objects.filter(post=post, choice=True).count()
            no_votes = Vote.objects.filter(post=post, choice=False).count()
            vote_result = {"yes": yes_votes, "no": no_votes}

            # ✅ 현재 계정 기준으로만 voted 여부 판단
            has_voted = False
            if request.user and request.user.is_authenticated:
                has_voted = Vote.objects.filter(post=post, user=request.user).exists()

            return Response({
                "success": True,
                "post": post_data,
                "comments": comment_data,
                "vote_result": vote_result,
                "has_voted": has_voted  # 🔥 이 값을 프론트에서 판단 기준으로 사용
            })

        except Post.DoesNotExist:
            return Response({
                "success": False,
                "message": "해당 게시글이 존재하지 않습니다."
            }, status=404)


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

        comment = Comment.objects.create(
            post=post,
            user=request.user,
            content=content
        )

        return Response({
            "success": True,
            "comment": CommentSerializer(comment).data  # ➤ userid  포함됨
        }, status=201)

#특정 게시글에 대한 댓글 리스트 조회 뷰 // front에서 "success":true 인 댓글만 가져가야 함
class CommentListByPostView(APIView):
    def get(self, request, post_id):
        comments = Comment.objects.filter(post_id=post_id, user__isnull=False).order_by('-created_at')

        if not comments.exists():
            return Response({
                "success": False,
                "message": "댓글이 존재하지 않습니다.",
                "data": []
            }, status=404)

        serializer = CommentSerializer(comments, many=True)
        return Response({
            "success": True,
            "message": "댓글 조회 성공",
            "data": serializer.data
        })

# 워드클라우드
class MonthlyKeywordAPIView(APIView):
    def get(self, request):
        month = request.GET.get("month")

        # 🔁 month가 없으면 가장 최신 달 자동 선택
        if not month:
            latest = MonthlyKeyword.objects.order_by("-month").first()
            if latest:
                month = latest.month
            else:
                return Response({"error": "데이터가 없습니다."}, status=404)

        # 🔎 해당 월 데이터 불러오기
        keywords = MonthlyKeyword.objects.filter(month=month).order_by("-score")[:100]
        result = [{"word": k.keyword, "score": round(k.score, 4)} for k in keywords]
        return Response({
            "month": month,
            "keywords": result
        })


#google 로그인
class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get("token")
        print("✅ 받은 토큰:", token)

        CLIENT_ID = "993737985073-qhthheoiruduqv4oaem4ao6evq4i4ovm.apps.googleusercontent.com"  # ⚠️ 반드시 실제 값으로 대체

        try:
            print("✅ CLIENT_ID:", CLIENT_ID)
            print("✅ 검증 시도 중...")
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
            print("✅ 검증 성공:", idinfo)

            email = idinfo["email"]
            name = idinfo.get("name", "사용자")  # 이름이 없을 경우 대비

            User = get_user_model()
            user, created = User.objects.get_or_create(userid=email, defaults={"name": name})
            print("✅ 사용자 생성 여부:", created)

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "userid": user.userid,
                "name": user.name
            })
        except Exception as e:
            print("❌ 구글 로그인 실패:", str(e))  # 여기에 실패 원인 출력됨
            return Response({"error": "유효하지 않은 토큰입니다."}, status=400)

# 사용자 정보 조회 API
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("📥 요청 헤더:", request.headers)
        print("🔐 인증된 유저:", request.user)
        return Response({
            "userid": request.user.userid,
            "name": request.user.name,
            "phone_num": request.user.phone_num,
        })
# 아래 2개 청원 예측 현황 용
class PredictionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionResult
        fields = ['id', 'petition_title', 'petition_content', 'prediction_percentage']

class PredictionResultListView(APIView):
    def get(self, request):
        results = PredictionResult.objects.all()
        serializer = PredictionResultSerializer(results, many=True)
        return Response(serializer.data)

