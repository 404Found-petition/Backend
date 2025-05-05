from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, History, PredictionResult, Vote, Post, Comment

# CustomUser 모델을 직렬화하는 클래스
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # 직렬화할 필드 정의
        fields = ['id', 'userid', 'name', 'nickname', 'phone_num', 'password']
        # password 필드는 쓰기 전용으로 설정하여 직렬화 시에만 사용되게 함
        extra_kwargs = {'password': {'write_only': True}}

    # 사용자가 생성될 때 password를 해싱하여 저장하는 create 메서드
    def create(self, validated_data):
        # 사용자 생성 시 해시된 비밀번호를 포함한 사용자 객체를 반환
        return CustomUser.objects.create_user(**validated_data)

# 사용자 로그인 시, 아이디와 비밀번호를 검증하는 클래스
class LoginSerializer(serializers.Serializer):
    # 로그인 시에 필요한 아이디와 비밀번호를 입력받음
    userid = serializers.CharField()
    password = serializers.CharField()

    # 사용자 인증을 위한 validate 메서드
    def validate(self, data):
        # authenticate 함수로 사용자 인증
        user = authenticate(userid=data.get('userid'), password=data.get('password'))
        # 인증 실패 시 ValidationError 발생
        if not user:
            raise serializers.ValidationError("아이디나 비밀번호를 다시 확인해주세요.")
        data['user'] = user  # 인증된 사용자 정보 추가
        return data

# History 모델을 직렬화하는 클래스
class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        # 모든 필드를 직렬화하여 반환
        fields = '__all__'

# PredictionResult 모델을 직렬화하는 클래스 (청원 예측 결과)
class PredictionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionResult
        # 모든 필드를 직렬화하여 반환
        fields = '__all__'

# Vote 모델을 직렬화하는 클래스 (투표 기능)
class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        # 모든 필드를 직렬화하여 반환
        fields = '__all__'

