from django.urls import path
from .views import (
    RegisterView,
    DeleteUserView,
    LoginView, 
    PetitionPredictView, 
    MyHistoryView, 
    wordcloud_data,
    wordcloud_months,
    wordcloud_data_tfidf,
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
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('delete-account/', DeleteUserView.as_view(), name='delete_account'),
    path('login/', LoginView.as_view(), name='login'),
    path('predict/', PetitionPredictView.as_view(), name='predict'),
    path('history/', MyHistoryView.as_view(), name='history'),
    path('check-duplicate/', check_duplicate, name='check_duplicate'),
    path('wordcloud/', wordcloud_data),
    path('wordcloud/tfidf/', wordcloud_data_tfidf),
    path('wordcloud/months/', wordcloud_months),
    path('petition-fields/', petition_field_stats, name='petition_fields'),
    path('prediction-results/', PredictionResultView.as_view(), name='prediction_results'),
    path('posts/create/', PostCreateView.as_view(), name='post_create'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='post_detail'),
    path('vote/', VoteView.as_view(), name='vote'),
    # 댓글 리스트 (GET)
    path('comments/<int:post_id>/list/', CommentListByPostView.as_view(), name='comment_list'),
    # 댓글 생성 (POST)
    path('comments/<int:post_id>/', CommentCreateView.as_view(), name='comment_create'),
    path('posts/page/', PostPaginationView.as_view(), name='post_pagination'),
    path('update-user/', UserUpdateView.as_view(), name='update_user'),
]
