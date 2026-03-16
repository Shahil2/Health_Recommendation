import json
import random
from datetime import date, timedelta
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count

from .models import BMIRecord, HealthProfile, MedicalReport, UserActivityTrack, Feedback
from .services.health_analyzer import generate_recommendations
from .services.report_analyzer import extract_report_content, analyze_medical_report
from .services.medicine_service import analyze_medicine
from .services.plan_service import generate_health_plans, generate_gym_workout, generate_home_workout, generate_yoga_workout
from .services.motivation_service import get_daily_motivation




# ---------------- HOME ----------------
@login_required(login_url='login')
def home(request):
    profile = HealthProfile.objects.filter(user=request.user).first()
    
    # Daily AI Motivation
    streak = profile.current_streak if profile else 0
    quote = get_daily_motivation(request.user, streak=streak)

    # Activity Data for Graph
    last_7_days = [(date.today() - timedelta(days=i)) for i in range(6, -1, -1)]
    activity_logs = UserActivityTrack.objects.filter(user=request.user, date__in=last_7_days)
    
    graph_labels = [d.strftime('%a') for d in last_7_days]
    graph_data = [] # Count of completed tasks per day
    for d in last_7_days:
        log = activity_logs.filter(date=d).first()
        score = 0
        if log:
            if log.workout_completed: score += 1
            if log.diet_followed: score += 1
            if log.medicine_taken: score += 1
        graph_data.append(score)

    # Today's Task Status
    today_log, created = UserActivityTrack.objects.get_or_create(user=request.user, date=date.today())
    
    # Check for simulated device connection
    device_connected = request.GET.get('device') == 'connected'
    device_stats = {
        'steps': random.randint(2000, 9000),
        'heart': random.randint(72, 88)
    } if device_connected else None

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
        'profile': profile,
        'quote': quote,
        'graph_labels': json.dumps(graph_labels),
        'graph_data': json.dumps(graph_data),
        'today_log': today_log,
        'device_connected': device_connected,
        'device_stats': device_stats,
    })

@login_required(login_url='login')
def toggle_activity(request, activity_type):
    today = date.today()
    log, created = UserActivityTrack.objects.get_or_create(user=request.user, date=today)
    
    if activity_type == 'workout':
        log.workout_completed = not log.workout_completed
    elif activity_type == 'diet':
        log.diet_followed = not log.diet_followed
    elif activity_type == 'medicine':
        log.medicine_taken = not log.medicine_taken
    
    log.save()
    
    # Update Streak
    profile = HealthProfile.objects.filter(user=request.user).first()
    if profile:
        yesterday = today - timedelta(days=1)
        if profile.last_streak_date == yesterday:
            # Continue streak if this is the first completion of the day
            if not (log.workout_completed or log.diet_followed or log.medicine_taken):
                 # If everything was unchecked, we don't necessarily break it yet,
                 # but if they complete SOMETHING today, and they completed SOMETHING yesterday, streak continues
                 pass
        
        # Simple streak logic: if ANY activity is done today, that counts for the day.
        # If they haven't updated in > 1 day, streak resets.
        if (log.workout_completed or log.diet_followed or log.medicine_taken):
            if profile.last_streak_date == yesterday:
                profile.current_streak += 1
            elif profile.last_streak_date != today:
                profile.current_streak = 1
            profile.last_streak_date = today
        else:
            # If they untick EVERYTHING for today
            if profile.last_streak_date == today:
                 # Check if they did anything else today if multiple logs existed (not possible with unique_together)
                 profile.current_streak = max(0, profile.current_streak - 1)
                 # This is tricky without a more complex history check, but let's keep it simple
                 profile.last_streak_date = yesterday
        
        profile.save()

    return redirect('home')


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


# ---------------- MEDICINE ANALYZER ----------------
@login_required(login_url='login')
def medicine_analyzer(request):
    result = None
    if request.method == 'POST':
        medicine_name = request.POST.get('medicine_name')
        medicine_image = request.FILES.get('medicine_image')
        
        if medicine_image:
            # Temporary save for AI analysis
            from django.core.files.storage import default_storage
            path = default_storage.save(f'tmp/{medicine_image.name}', medicine_image)
            full_path = default_storage.path(path)
            result = analyze_medicine(image_path=full_path)
            default_storage.delete(path) # Cleanup
        elif medicine_name:
            result = analyze_medicine(medicine_name=medicine_name)
        else:
            messages.error(request, "Please enter a name or upload a photo.")

    return render(request, 'healthapp/medicine_analyzer.html', {'result': result})


# ---------------- HEALTH PLANS ----------------
@login_required(login_url='login')
def health_plans(request):
    profile = HealthProfile.objects.filter(user=request.user).first()
    
    if not profile:
        messages.warning(request, "Please complete your Health Profile first to get personalized plans.")
        return redirect('health_profile')

    plans = generate_health_plans(profile)
    return render(request, 'healthapp/health_plans.html', {'plans': plans})


# ---------------- GYM WORKOUT ----------------
@login_required(login_url='login')
def gym_workout(request):
    profile = HealthProfile.objects.filter(user=request.user).first()
    
    if not profile:
        messages.warning(request, "Please complete your Health Profile first to get a personalized routine.")
        return redirect('health_profile')

    mode = request.GET.get('mode') # medical or normal
    workout_type = request.GET.get('type') # gym or home
    
    workout = None
    if mode and workout_type:
        if workout_type == 'gym':
            workout = generate_gym_workout(profile, mode=mode)
        else:
            workout = generate_home_workout(profile, mode=mode)

    return render(request, 'healthapp/gym_workout.html', {
        'workout': workout, 
        'mode': mode,
        'type': workout_type
    })


# ---------------- HOME WORKOUT ----------------
@login_required(login_url='login')
def home_workout(request):
    return redirect('gym_workout')
@login_required(login_url='login')
def device_sync(request):
    # Simulated status check (will be connected via JS bridge later)
    is_connected = request.GET.get('connected') == 'true'
    
    # Random data for demonstration
    stats = {
        'heart_rate': random.randint(70, 95) if is_connected else 0,
        'steps': random.randint(1500, 8000) if is_connected else 0,
        'calories': random.randint(100, 500) if is_connected else 0,
        'sleep_hours': round(random.uniform(6.0, 8.5), 1) if is_connected else 0.0,
        'blood_pressure': "120/80" if is_connected else "--/--"
    }
    
    return render(request, 'healthapp/device_sync.html', {
        'is_connected': is_connected,
        'stats': stats
    })
@login_required(login_url='login')
def yoga(request):
    profile = HealthProfile.objects.filter(user=request.user).first()
    
    if not profile:
        messages.warning(request, "Please complete your Health Profile first to get a personalized Yoga journey.")
        return redirect('health_profile')

    mode = request.GET.get('mode', 'normal') # medical or normal
    yoga_plan = generate_yoga_workout(profile, mode=mode)

    return render(request, 'healthapp/yoga.html', {
        'yoga_plan': yoga_plan,
        'mode': mode,
    })
@login_required(login_url='login')
def motivation(request):
    profile = HealthProfile.objects.filter(user=request.user).first()
    streak = profile.current_streak if profile else 0
    
    # Generate 3 power quotes
    quotes = [get_daily_motivation(request.user, streak=streak) for _ in range(3)]
    
    return render(request, 'healthapp/motivation.html', {
        'quotes': quotes,
        'streak': streak
    })

@login_required(login_url='login')
def feedback(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        Feedback.objects.create(
            user=request.user,
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Send email to developer (staff users)
        try:
            staff_emails = [u.email for u in User.objects.filter(is_staff=True) if u.email]
            if staff_emails:
                send_mail(
                    subject=f"New App Feedback: {subject}",
                    message=f"From: {name} ({email})\n\nMessage:\n{message}",
                    from_email=None,
                    recipient_list=staff_emails,
                    fail_silently=True,
                )
        except:
            pass

        messages.success(request, "Thank you for your feedback! It has been sent to the developer.")
        return redirect('home')
        
    return render(request, 'healthapp/feedback.html')
