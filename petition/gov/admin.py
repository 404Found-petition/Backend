from django.contrib import admin
from .models import CustomUser, History

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(History)