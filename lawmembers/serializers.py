from rest_framework import serializers
from .models import Lawmaker, Bill

FIELD_COLORS = {
    "정치·행정": "#70B7FF",
    "사회": "#B1FF9A",
    "경제·산업": "#F2B856",
    "교육": "#FFF12B",
    "환경": "#42D583",
    "교통·건설": "#F9A3D4",
    "보건·의료": "#FF5A4E",
    "문화·예술": "#CBA0FF",
    "과학·기술": "#33E4FF",
    "국방·외교": "#538F2D",
    "기타": "#AAAAAA"
}

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['title']

class LawmakerSerializer(serializers.ModelSerializer):
    bills = BillSerializer(many=True, read_only=True)
    color = serializers.SerializerMethodField()  # ✅ 여기에 색상 필드 추가

    class Meta:
        model = Lawmaker
        fields = ['id', 'name', 'party', 'representative_field', 'seat_number', 'photo', 'bills', 'color']

    def get_color(self, obj):
        return FIELD_COLORS.get(obj.representative_field, "#AAAAAA")  # 기본값: 회색
