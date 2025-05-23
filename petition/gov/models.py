from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


# Custom user manager for creating and managing CustomUser
class CustomUserManager(BaseUserManager):
    def create_user(self, userid, password=None, **extra_fields):
        # 아이디가 없으면 ValueError를 발생시킴
        if not userid:
            raise ValueError('아이디는 필수입니다.')
        user = self.model(userid=userid, **extra_fields)  # 사용자 객체 생성
        user.set_password(password)  # 비밀번호를 해시하여 저장
        user.save(using=self._db)  # 데이터베이스에 저장
        return user

    def create_superuser(self, userid, password=None, **extra_fields):
        # 슈퍼유저가 생성될 때 필요한 기본 필드를 설정
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # 슈퍼유저 조건 검증
        if extra_fields.get('is_staff') is not True:
            raise ValueError('슈퍼유저는 is_staff=True 이어야 합니다.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('슈퍼유저는 is_superuser=True 이어야 합니다.')

        # 슈퍼유저 생성
        return self.create_user(userid, password, **extra_fields)

# CustomUser 모델 정의 (기본 사용자 모델)
class CustomUser(AbstractBaseUser, PermissionsMixin):
    # 사용자 아이디 필드 (unique하게 설정)
    userid = models.CharField(max_length=50, unique=True)
    # 사용자 이름, 전화번호 필드
    name = models.CharField(max_length=50)
    phone_num = models.CharField(max_length=20)

    # 기본 활성화 여부, staff 권한 설정
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # 사용자 관리 매니저 설정
    objects = CustomUserManager()

    # 로그인에 사용할 필드 설정
    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['name', 'nickname']

    def __str__(self):
        return self.userid

# History 모델 - 사용자의 예측 기록을 저장하는 모델
class History(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='history')  # related_name 추가
    search_petition = models.TextField()  # 검색된 청원 텍스트
    search_petition_percentage = models.FloatField()  # 예측 확률
    history_date = models.DateTimeField(auto_now_add=True)  # 예측 기록 작성 시간

    def __str__(self):
        return f"{self.user} - {self.search_petition} ({self.history_date})"

# UserPrediction 모델 - 청원 예측 결과를 저장하는 모델 (이름바꿈)
class UserPrediction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    petition_title = models.CharField(max_length=200)
    petition_content = models.TextField()
    prediction_percentage = models.FloatField()
    predicted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.petition_title} ({self.prediction_percentage}%)"

# Vote 모델 - 사용자가 게시글에 대해 찬반 투표를 할 수 있는 모델
class Vote(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes')  # 🔧 수정
    choice = models.BooleanField()

    class Meta:
        unique_together = ('post', 'user')

        
# Post 모델 - 게시글을 작성하는 모델
class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')  # related_name 추가
    title = models.CharField(max_length=200)  # 게시글 제목
    content = models.TextField()  # 게시글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 게시글 작성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 게시글 수정 시간
    has_poll = models.BooleanField(default=False)  # 찬반투표 활성화 여부

    def __str__(self):
        return self.title  # 게시글 제목 반환

# Comment 모델 - 게시글에 대한 댓글을 작성하는 모델
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')  # related_name 추가
    post = models.ForeignKey(Post, on_delete=models.CASCADE)  # 해당 댓글이 속한 게시글
    content = models.TextField()  # 댓글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 댓글 작성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 댓글 수정 시간

    def __str__(self):
        return self.content  # 댓글 내용 반환

class Petition(models.Model):
    title = models.CharField(max_length=300)  # 청원 제목
    content = models.TextField(blank=True, null=True)  # 청원 내용
    agreement_percentage = models.FloatField()  # 동의율 퍼센트
    created_at = models.DateTimeField(auto_now_add=True)  # 생성일

    def __str__(self):
        return self.title
    
# 워드 클라우드 요약 저장
class PetitionSummary(models.Model):
    title = models.CharField(max_length=300)
    summary = models.TextField()
    created_at = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.created_at}"

# 워드 클라우드 월별 저장
class MonthlyKeyword(models.Model):
    month = models.CharField(max_length=7)  # e.g., '2024-04'
    keyword = models.CharField(max_length=100)
    score = models.FloatField()

    class Meta:
        unique_together = ('month', 'keyword')