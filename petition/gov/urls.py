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
    VoteView,
    PostPaginationView,
    UserUpdateView,
    CommentListByPostView,
    PostDetailView,
    PostCreateView,
    CommentCreateView,
    PetitionPaginationView,     
    GoogleLoginView,  # ✅ 추가
    MonthlyKeywordAPIView,
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
    path('prediction-results/', PredictionResultView.as_view(), name='prediction_results'),
    path('posts/create/', PostCreateView.as_view(), name='post_create'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('vote/', VoteView.as_view(), name='vote'),
    path('comments/<int:post_id>/list/', CommentListByPostView.as_view(), name='comment_list'),
    path('comments/<int:post_id>/', CommentCreateView.as_view(), name='comment_create'),
    path('posts/', PostPaginationView.as_view(), name='post_list'),
    path('update-user/', UserUpdateView.as_view(), name='update_user'),
    path("monthly-keywords/", MonthlyKeywordAPIView.as_view(), name="monthly-keywords"),
    # ✅ Google 로그인 경로 추가
    path('social-login/google/', GoogleLoginView.as_view(), name='google_login'),
    
]
