from django.urls import path
from .views import (
    RegisterView,
    DeleteUserView,
    LoginView, 
    PetitionPredictView, 
    MyHistoryView, 
    check_duplicate,
    petition_field_stats,
    PredictionResultView,
    PredictionResultListView,
    VoteView,
    PostPaginationView,
    UserUpdateView,
    CommentListByPostView,
    PostDetailView,
    PostCreateView,
    CommentCreateView,
    PetitionPaginationView,     
    GoogleLoginView,
    MonthlyKeywordAPIView,
    CurrentUserView, # ✅ 사용자 정보 조회 뷰 임포트
    MyPostListView,  # ✅ 추가
    MyPredictionListView, # ✅ 추가
    RecentPostsAPIView,
    MyRecentPostsView,
    LawmakerAPIProxyView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('delete-account/', DeleteUserView.as_view(), name='delete_account'),
    path('login/', LoginView.as_view(), name='login'),
    path('predict/', PetitionPredictView.as_view(), name='predict'),
    path('history/', MyHistoryView.as_view(), name='history'),
    path('check-duplicate/', check_duplicate, name='check_duplicate'),
    path("wordcloud/", MonthlyKeywordAPIView.as_view(), name="wordcloud"),
    path('petition-fields/', petition_field_stats, name='petition_fields'),
    path('petitions/page/', PetitionPaginationView.as_view(), name='petition_pagination'),
    path('predictions/', PredictionResultListView.as_view(), name='prediction_results'),
    #path('prediction-results/', PredictionResultView.as_view(), name='prediction_results'),
    path('posts/create/', PostCreateView.as_view(), name='post_create'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('vote/', VoteView.as_view(), name='vote'),
    path('comments/<int:post_id>/list/', CommentListByPostView.as_view(), name='comment_list'),
    path('comments/<int:post_id>/', CommentCreateView.as_view(), name='comment_create'),
    path('posts/', PostPaginationView.as_view(), name='post_list'),
    path('update-user/', UserUpdateView.as_view(), name='update_user'),
    path("monthly-keywords/", MonthlyKeywordAPIView.as_view(), name="monthly-keywords"),
    path('social-login/google/', GoogleLoginView.as_view(), name='google_login'),
    path('posts/recent/', RecentPostsAPIView.as_view()),
    path("api/lawmaker-info/", LawmakerAPIProxyView.as_view(), name="lawmaker-info"),

    # ✅ 현재 로그인한 사용자 정보 조회
    path('user/', CurrentUserView.as_view(), name='current_user'),
    path('posts/mine/', MyPostListView.as_view(), name='my_posts'), #사용자 작성 게시글 목록 
    path('posts/mine/recent/', MyRecentPostsView.as_view(), name='my_recent_posts'), #사용자가 작성한 최근 4개 게시물물
    path('my-predictions/', MyPredictionListView.as_view(), name='my_predictions'),
]
