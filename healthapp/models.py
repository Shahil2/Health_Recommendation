from django.db import models
from django.contrib.auth.models import User

class BMIRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    height = models.FloatField()
    weight = models.FloatField()
    bmi = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.bmi}"


class HealthProfile(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    ACTIVITY_LEVELS = [
        ('Low', 'Low'),
        ('Moderate', 'Moderate'),
        ('High', 'High'),
    ]

    SUGAR_STATUS_CHOICES = [
        ('Normal', 'Normal'),
        ('Prediabetes', 'Prediabetes'),
        ('Diabetes', 'Diabetes'),
    ]

    SUGAR_TEST_TYPE_CHOICES = [
        ('Fasting', 'Fasting'),
        ('Random', 'Random'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")

    blood_pressure = models.CharField(max_length=15)

    sugar_level = models.FloatField(help_text="mg/dL")
    sugar_status = models.CharField(max_length=15, choices=SUGAR_STATUS_CHOICES)
    sugar_test_type = models.CharField(max_length=10, choices=SUGAR_TEST_TYPE_CHOICES)

    activity_level = models.CharField(max_length=10, choices=ACTIVITY_LEVELS)

    smoker = models.BooleanField(default=False)
    alcohol = models.BooleanField(default=False)

    sleep_hours = models.FloatField(default=7.0)

    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Health Profile"

