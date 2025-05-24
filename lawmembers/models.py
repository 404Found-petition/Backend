from django.db import models

class Lawmaker(models.Model):
    name = models.CharField(max_length=50, unique=True)
    party = models.CharField(max_length=100)
    representative_field = models.CharField(max_length=100)
    seat_number = models.IntegerField(unique=True)
    photo = models.URLField(blank=True, null=True)  # ✅ 수정: 외부 URL 저장 가능

    def __str__(self):
        return f"{self.seat_number}번 - {self.name}"

class Bill(models.Model):
    lawmaker = models.ForeignKey(Lawmaker, on_delete=models.CASCADE, related_name='bills')
    title = models.CharField(max_length=300)
