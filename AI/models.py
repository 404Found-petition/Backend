# ai/models.py
from django.db import models

class PredictionResult(models.Model):
    title = models.CharField(max_length=200)      # 청원제목
    summary = models.TextField()                  # 청원내용
    probability = models.FloatField()             # 승인 확률 (0~100)

    def __str__(self):
        return f"{self.title} - {self.probability}%"


