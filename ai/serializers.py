# ai/serializers.py
from rest_framework import serializers
from .models import CsvPrediction

class CsvPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CsvPrediction
        fields = ['id', 'title', 'summary', 'probability']
