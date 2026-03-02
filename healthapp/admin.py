from django.contrib import admin
from .models import BMIRecord, HealthProfile, MedicalReport

admin.site.register(BMIRecord)
admin.site.register(HealthProfile)
admin.site.register(MedicalReport)
