from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, History

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'userid', 'name', 'nickname', 'phone_num', 'password']
        extra_kwargs = {'password': {'write_only': True}}

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

class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = '__all__'