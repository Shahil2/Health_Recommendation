from django.urls import path
from . import views

urlpatterns = [
    # Home / BMI Dashboard
    path('', views.home, name='home'),

    # Authentication
    path('login/', views.login_user, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_user, name='logout'),

    # Health Profile Analyzer
    path('health-profile/', views.health_profile, name='health_profile'),

    # Medical Reports (upload, list, detail)
    path('reports/', views.report_list, name='report_list'),
    path('reports/upload/', views.report_upload, name='report_upload'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),

    # NEW: Medicine & Health Plans
    path('medicine-analyzer/', views.medicine_analyzer, name='medicine_analyzer'),
    path('health-plans/', views.health_plans, name='health_plans'),
    path('gym-workout/', views.gym_workout, name='gym_workout'),
    path('home-workout/', views.home_workout, name='home_workout'),
    path('toggle-activity/<str:activity_type>/', views.toggle_activity, name='toggle_activity'),
    path('device-sync/', views.device_sync, name='device_sync'),
    path('yoga/', views.yoga, name='yoga'),
    path('motivation/', views.motivation, name='motivation'),
    path('feedback/', views.feedback, name='feedback'),
]
