from django.db import models

class PetitionSummaryCategory(models.Model):
    청원제목 = models.CharField(max_length=255)
    청원요지 = models.TextField()
    분야 = models.CharField(max_length=50)

    class Meta:
        verbose_name = "분류된 청원요지"
        verbose_name_plural = "분류된 청원요지 모음"

    def __str__(self):
        return f"{self.청원제목} ({self.분야})"
