import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from .models import BMIRecord, HealthProfile, MedicalReport
from .services.health_analyzer import generate_recommendations
from .services.report_analyzer import extract_report_content, analyze_medical_report




# ---------------- HOME ----------------
@login_required(login_url='login')
def home(request):
    bmi = status = tip = None
    history = BMIRecord.objects.filter(user=request.user).order_by('-date')[:5]

    if request.method == 'POST':
        try:
            height = float(request.POST.get('height', 0))
            weight = float(request.POST.get('weight', 0))

            if height <= 0 or weight <= 0:
                raise ValueError

            bmi = round(weight / ((height / 100) ** 2), 2)

            BMIRecord.objects.create(
                user=request.user,
                height=height,
                weight=weight,
                bmi=bmi
            )

            if bmi < 18.5:
                status = "Underweight"
                tip = "Focus on nutritious meals."
            elif bmi < 25:
                status = "Healthy"
                tip = "Maintain your lifestyle."
            elif bmi < 30:
                status = "Overweight"
                tip = "Increase physical activity."
            else:
                status = "Obese"
                tip = "Consult a doctor."

        except (ValueError, TypeError):
            messages.error(request, "Invalid input. Please enter valid numbers for height and weight.")

    return render(request, 'healthapp/home.html', {
        'bmi': bmi,
        'status': status,
        'tip': tip,
        'history': history,
    })


# ---------------- HEALTH PROFILE ----------------
@login_required(login_url='login')
def health_profile(request):
    profile = HealthProfile.objects.filter(user=request.user).first()

    bmi = score = None
    feedback = ""
    recommendations = None

    if request.method == 'POST':
        try:
            age = int(request.POST.get('age', 0))
            gender = request.POST.get('gender', '')
            height = float(request.POST.get('height', 0))
            weight = float(request.POST.get('weight', 0))
            blood_pressure = request.POST.get('blood_pressure', '')

            sugar_level = float(request.POST.get('sugar_level', 0))
            sugar_status = request.POST.get('sugar_status', '')
            sugar_test_type = request.POST.get('sugar_test_type', '')

            activity_level = request.POST.get('activity_level', '')
            smoker = request.POST.get('smoker') == 'on'
            alcohol = request.POST.get('alcohol') == 'on'
            sleep_hours = float(request.POST.get('sleep_hours', 0))

            if height <= 0 or weight <= 0:
                raise ValueError

            # -------- BMI --------
            bmi = round(weight / ((height / 100) ** 2), 2)

            # -------- RISK CALCULATION --------
            risk = 0
            if bmi < 18.5 or bmi > 30:
                risk += 20
            if sugar_status == "Diabetes":
                risk += 25
            elif sugar_status == "Prediabetes":
                risk += 15
            if smoker:
                risk += 15
            if alcohol:
                risk += 10
            if sleep_hours < 6:
                risk += 10
            if activity_level == "Low":
                risk += 10

            score = max(0, 100 - risk)

            # -------- FEEDBACK --------
            if score >= 80:
                feedback = "Excellent health."
            elif score >= 60:
                feedback = "Good health."
            elif score >= 40:
                feedback = "Moderate risk."
            else:
                feedback = "High risk."

            # -------- SAVE / UPDATE PROFILE --------
            profile, _ = HealthProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    'age': age,
                    'gender': gender,
                    'height': height,
                    'weight': weight,
                    'blood_pressure': blood_pressure,
                    'sugar_level': sugar_level,
                    'sugar_status': sugar_status,
                    'sugar_test_type': sugar_test_type,
                    'activity_level': activity_level,
                    'smoker': smoker,
                    'alcohol': alcohol,
                    'sleep_hours': sleep_hours,
                }
            )

            # -------- AI + RULE-BASED RECOMMENDATIONS --------
            
            recommendations = generate_recommendations(
                profile=profile,
                bmi=bmi,
                score=score
            )
            messages.success(request, "Health profile analyzed successfully!")

        except (ValueError, TypeError):
            messages.error(request, "Please fill all fields correctly.")

    return render(request, 'healthapp/health_profile.html', {
        'profile': profile,
        'bmi': bmi,
        'score': score,
        'feedback': feedback,
        'recommendations': recommendations,
    })

# ---------------- AUTH ----------------
def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        User.objects.create_user(username=username, email=email, password=password1)
        messages.success(request, "Account created successfully!")
        return redirect('login')

    return render(request, 'healthapp/signup.html')


def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')

        messages.error(request, "Invalid credentials.")

    return render(request, 'healthapp/login.html')


def logout_user(request):
    logout(request)
    return redirect('login')


# ---------------- MEDICAL REPORTS ----------------
@login_required(login_url='login')
def report_upload(request):
    """Upload medical report (PDF or image) for analysis."""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('report_file')
        if not uploaded_file:
            messages.error(request, "Please select a file.")
            return redirect('report_upload')

        ext = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
        if ext not in ('pdf', 'png', 'jpg', 'jpeg', 'webp'):
            messages.error(request, "Only PDF, PNG, and JPG files are allowed.")
            return redirect('report_upload')

        if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB
            messages.error(request, "File size must be under 10 MB.")
            return redirect('report_upload')

        report = MedicalReport.objects.create(user=request.user, file=uploaded_file)
        file_path = report.file.path

        text, content_type = extract_report_content(file_path)
        if content_type is None:
            messages.error(request, "Unsupported file format.")
            report.delete()
            return redirect('report_upload')

        report.raw_text = text if content_type == "text" else "[Image - analyzed by AI vision]"
        report.save()

        result = analyze_medical_report(file_path, extracted_text=text, is_image=(content_type == "image"))
        report.summary = result.get("summary", "")
        report.lifestyle_advice = result.get("lifestyle_advice", "")
        report.medicine_suggestions = result.get("medicine_suggestions", "")
        report.doctor_suggestions = result.get("doctor_suggestions", "")
        report.conditions_notes = result.get("conditions_notes", "")
        report.extracted_metrics = result.get("extracted_metrics", [])
        report.lifestyle_plan = result.get("lifestyle_plan", [])
        report.workout_plan = result.get("workout_plan", [])
        report.diet_plan = result.get("diet_plan", [])
        report.save()

        messages.success(request, "Report analyzed successfully!")
        return redirect('report_detail', report_id=report.pk)

    return render(request, 'healthapp/report_upload.html')


@login_required(login_url='login')
def report_list(request):
    """List all medical reports for the current user."""
    reports = MedicalReport.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'healthapp/report_list.html', {'reports': reports})


@login_required(login_url='login')
def report_detail(request, report_id):
    """View details and AI analysis for a single report."""
    report = MedicalReport.objects.filter(user=request.user, pk=report_id).first()
    if not report:
        messages.error(request, "Report not found.")
        return redirect('report_list')
    metrics = getattr(report, 'extracted_metrics', None) or []
    return render(request, 'healthapp/report_detail.html', {
        'report': report,
        'metrics_json': json.dumps(metrics),
    })
