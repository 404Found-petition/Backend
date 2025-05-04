from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    PetitionPredictView, 
    MyHistoryView, 
    wordcloud_data,
    wordcloud_months,
    wordcloud_data_tfidf,
    check_duplicate,
    petition_field_stats
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('predict/', PetitionPredictView.as_view(), name='predict'),
    path('history/', MyHistoryView.as_view(), name='history'),
    path('check-duplicate/', check_duplicate, name='check_duplicate'),
    path('wordcloud/', wordcloud_data),
    path('wordcloud/tfidf/', wordcloud_data_tfidf),
    path('wordcloud/months/', wordcloud_months),
    path('petition-fields/', petition_field_stats, name='petition_fields'),
]
