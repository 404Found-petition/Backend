from django.contrib import admin
from .models import CustomUser, History, PredictionResult

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(History)
admin.site.register(PredictionResult)