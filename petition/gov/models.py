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
    # 사용자 이름, 닉네임, 전화번호 필드
    name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=50, unique=True)
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    search_petition = models.CharField(max_length=200)  # 청원 내용
    search_petition_percentage = models.FloatField()  # 예측 결과
    history_date = models.DateTimeField(auto_now_add=True)  # 예측한 시간

# PredictionResult 모델 - 청원 예측 결과를 저장하는 모델
class PredictionResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    petition_title = models.CharField(max_length=300)  # 청원 제목
    petition_content = models.TextField(null=True, blank=True)  # 청원 내용 (optional)
    prediction_percentage = models.FloatField()  # 예측된 이행 확률
    predicted_at = models.DateTimeField(auto_now_add=True)  # 예측이 이루어진 시간

    def __str__(self):
        return f"{self.petition_title} - {self.prediction_percentage:.2f}%"  # 청원 제목과 예측 확률을 반환

# Vote 모델 - 사용자가 게시글에 대해 찬반 투표를 할 수 있는 모델
class Vote(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)  # 게시글과 연결
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    choice = models.BooleanField()  # True=찬성, False=반대

    class Meta:
        unique_together = ('post', 'user')  # 하나의 게시글에 대해 중복된 투표를 방지

# Post 모델 - 게시글을 작성하는 모델
class Post(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    title = models.CharField(max_length=200)  # 게시글 제목
    content = models.TextField()  # 게시글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 게시글 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 게시글 수정 시간

    def __str__(self):
        return self.title  # 게시글 제목을 반환

# Comment 모델 - 게시글에 대한 댓글을 작성하는 모델
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')  # 게시글과 연결 (댓글들)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 사용자와 연결
    content = models.TextField()  # 댓글 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 댓글 작성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 댓글 수정 시간

    def __str__(self):
        return f"댓글 by {self.user.nickname} on {self.post.title}"  # 댓글 작성자와 게시글 제목을 반환
