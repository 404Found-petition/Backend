from django.db import models

class FieldSummary(models.Model):
    분야 = models.CharField(max_length=50, unique=True)
    청원수 = models.IntegerField()
    색상 = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.분야} ({self.청원수})"

