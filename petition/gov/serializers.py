from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, History, PredictionResult, Vote, Post, Comment, Petition


# -------------------- 사용자 관련 --------------------
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'userid', 'name', 'phone_num', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'name': {'read_only': True}
        }

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    userid = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(userid=data.get('userid'), password=data.get('password'))
        if not user:
            raise serializers.ValidationError("아이디나 비밀번호를 다시 확인해주세요.")
        data['user'] = user
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['name', 'phone_num', 'password', 'password_confirm']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def validate(self, data):
        password = data.get("password")
        password_confirm = data.get("password_confirm")

        if password and password != password_confirm:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.phone_num = validated_data.get("phone_num", instance.phone_num)
        password = validated_data.get("password", None)

        if password:
            instance.set_password(password)
        instance.save()
        return instance


# -------------------- 게시글 관련 --------------------
class CommentSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d')

    class Meta:
        model = Comment
        fields = ['nickname', 'content', 'date']

    def get_nickname(self, obj):
        return obj.user.name if obj.user and obj.user.name else "익명"


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    userid = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'created_at', 'userid', 'comments']

    def get_userid(self, obj):
        return obj.user.userid if obj.user else "익명"

    def get_comments(self, obj):
        comments = Comment.objects.filter(post=obj).order_by('-created_at')[:2]
        return CommentSerializer(comments, many=True).data


# -------------------- 청원 관련 --------------------
class PetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Petition
        fields = '__all__'


# -------------------- 예측 관련 --------------------
class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = '__all__'


class PredictionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionResult
        fields = ['id', 'petition_title', 'petition_content', 'prediction_percentage', 'predicted_at']


# -------------------- 투표 관련 --------------------
class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = '__all__'
