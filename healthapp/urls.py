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
]
