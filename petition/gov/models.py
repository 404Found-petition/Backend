from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, userid, password=None, **extra_fields):
        if not userid:
            raise ValueError('아이디는 필수입니다.')
        user = self.model(userid=userid, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, userid, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('슈퍼유저는 is_staff=True 이어야 합니다.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('슈퍼유저는 is_superuser=True 이어야 합니다.')

        return self.create_user(userid, password, **extra_fields)
    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    userid = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=50, unique=True)
    phone_num = models.CharField(max_length=20)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['name', 'nickname']

    def __str__(self):
        return self.userid

class History(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    search_petition = models.CharField(max_length=200)
    search_petition_percentage = models.FloatField()
    history_date = models.DateTimeField(auto_now_add=True)