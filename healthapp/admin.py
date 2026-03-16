from django.contrib import admin
from .models import BMIRecord, HealthProfile, MedicalReport, UserActivityTrack, Feedback

admin.site.register(BMIRecord)
admin.site.register(HealthProfile)
admin.site.register(MedicalReport)
admin.site.register(UserActivityTrack)
admin.site.register(Feedback)
