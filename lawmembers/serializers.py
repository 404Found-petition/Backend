from rest_framework import serializers
from .models import Lawmaker, Bill

class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['title']

class LawmakerSerializer(serializers.ModelSerializer):
    bills = BillSerializer(many=True, read_only=True)

    class Meta:
        model = Lawmaker
        fields = ['id', 'name', 'party', 'representative_field', 'seat_number', 'photo', 'bills']