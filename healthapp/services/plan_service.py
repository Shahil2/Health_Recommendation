import google.generativeai as genai
from django.conf import settings
import json
import re
from ..models import MedicalReport

def generate_health_plans(profile, mode='normal', goal=None, report_id=None):
    """
    Generate personalized workout and diet plans using Gemini based on HealthProfile.
    Modes: 'normal' (goal-based), 'medical' (report-based)
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    print(f"DEBUG: Initializing model models/gemini-flash-latest for health plans ({mode})")
    model = genai.GenerativeModel("models/gemini-flash-latest")

    profile_data = f"""
    Age: {profile.age}
    Gender: {profile.gender}
    Weight: {profile.weight} kg
    Height: {profile.height} cm
    Activity Level: {profile.activity_level}
    Sugar Status: {profile.sugar_status}
    Smoker: {profile.smoker}
    Alcohol: {profile.alcohol}
    Sleep: {profile.sleep_hours} hours
    BP: {profile.blood_pressure}
    """

    report_context = ""
    report = None
    if mode == 'medical':
        if report_id:
            report = MedicalReport.objects.filter(user=profile.user, id=report_id).first()
        if not report:
            report = MedicalReport.objects.filter(user=profile.user).order_by('-uploaded_at').first()
            
        if report:
            report_context = f"LATEST MEDICAL REPORT FINDINGS: {report.conditions_notes}\nSUMMARY: {report.summary}"

    if mode == 'medical':
        prompt_goal = "HEALING & SAFETY. Adapt both diet and workout to address risks found in the medical report. Suggest foods that help with their conditions."
    else:
        goal_text = f" Specifically focus on this goal: {goal}." if goal else " Focus on general health maintenance."
        prompt_goal = f"NUTRITION & FITNESS GOALS.{goal_text}"

    prompt = f"""
    Act as a professional fitness coach and nutritionist.
    Based on this profile and goals, generate a 7-day Health Plan (Diet + basic home workout).
    
    MODE: {mode.upper()}
    GOAL: {prompt_goal}
    
    Profile:
    {profile_data}
    {report_context}
    
    Provide the output in the following JSON format:
    {{
        "workout_plan": [
            {{ "day": "Day 1", "activities": ["ex1", "ex2"], "duration": "30 mins" }},
            ... for 7 days
        ],
        "diet_plan": [
            {{ "meal": "Breakfast", "options": ["Option 1", "Option 2"], "avoid": ["Sugar", "Fried"] }},
            {{ "meal": "Lunch", "options": ["Option 1", "Option 2"], "avoid": ["Oil"] }},
            {{ "meal": "Dinner", "options": ["Option 1", "Option 2"], "avoid": ["Heavy food"] }}
        ],
        "lifestyle_tips": ["Tip 1", "Tip 2"]
    }}
    
    Keep it extremely simple and easy to follow. Focus on home workouts.
    """

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Parse JSON
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
        if match:
            return json.loads(match.group(1))
        
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))

        return {"error": "Failed to parse AI plans."}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Always fallback to default plan if API fails
        return {
            "workout_plan": [
                {"day": f"Day {i}", "activities": ["Stretching", "Walking", "Basic Squats"], "duration": "20 mins"} for i in range(1, 8)
            ],
            "diet_plan": [
                {"meal": "Breakfast", "options": ["Oatmeal with fruit", "Whole grain toast"], "avoid": ["Sugary cereals"]},
                {"meal": "Lunch", "options": ["Grilled chicken salad", "Quinoa bowl"], "avoid": ["Soft drinks"]},
                {"meal": "Dinner", "options": ["Baked fish", "Steamed vegetables"], "avoid": ["Heavy sauces"]}
            ],
            "lifestyle_tips": ["Stay hydrated throughout the day.", "Aim for 8 hours of sleep.", "Don't stress, our AI is just taking a short break."]
        }

def generate_gym_workout(profile, mode='normal', focus=None, report_id=None):
    """
    Generate a professional Gym-specific workout plan.
    Modes: 'normal' (maintenance), 'medical' (based on report issues)
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    print(f"DEBUG: Initializing model models/gemini-flash-latest for gym workout ({mode})")
    model = genai.GenerativeModel("models/gemini-flash-latest")

    report_context = ""
    report = None
    if mode == 'medical':
        if report_id:
            report = MedicalReport.objects.filter(user=profile.user, id=report_id).first()
        if not report:
            report = MedicalReport.objects.filter(user=profile.user).order_by('-uploaded_at').first()
        if report:
            report_context = f"LATEST MEDICAL REPORT FINDINGS: {report.conditions_notes}\nSUMMARY: {report.summary}"

    profile_data = f"""
    Age: {profile.age}, Gender: {profile.gender}, Weight: {profile.weight}kg, Activity: {profile.activity_level}, Sugar: {profile.sugar_status}
    """

    focus_text = f" Specifically focus on this goal: {focus}." if focus else ""
    if mode == 'medical':
        prompt_goal = f"HEALING & SAFETY. Adapt activities to address risks found in the medical report (e.g. low impact if joint issues, steady cardio if BP high).{focus_text}"
    else:
        prompt_goal = f"BODY MAINTENANCE & TARGETED GOALS. Focus on general fitness, muscle tone, and metabolism.{focus_text}"

    prompt = f"""
    Act as a professional Gym Trainer. Create a 7-day Gym Workout Plan.
    MODE: {mode.upper()}
    GOAL: {prompt_goal}
    
    Profile: {profile_data}
    {report_context}
    
    The plan must use GYM EQUIPMENT (Barbells, Dumbbells, Machines, Cables).
    
    Provide output in JSON:
    {{
        "title": "{mode.capitalize()} Gym Routine",
        "description": "7-day customized routine for {mode} needs.",
        "days": [
            {{
                "day": "Monday",
                "focus": "...",
                "exercises": [
                    {{ "name": "...", "sets": "3", "reps": "12", "tip": "..." }}
                ]
            }},
            ...
        ]
    }}
    Include 1-2 rest days.
    """

    try:
        response = model.generate_content(prompt)
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response.text)
        if match:
            return json.loads(match.group(1))
        
        match = re.search(r"\{[\s\S]*\}", response.text)
        if match:
            return json.loads(match.group(0))

        return {"error": "AI could not generate gym plan."}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {
            "title": "Essential Gym Routine (Free Mode)",
            "description": "A high-quality fallback routine focusing on core compound movements (AI is currently resting).",
            "days": [
                {"day": "Monday", "focus": "Upper Body", "exercises": [{"name": "Bench Press", "sets": "3", "reps": "12", "tip": "Control the descent"}]},
                {"day": "Tuesday", "focus": "Lower Body", "exercises": [{"name": "Leg Press", "sets": "3", "reps": "15", "tip": "Drive through heels"}]},
                {"day": "Wednesday", "focus": "Rest", "exercises": []},
                {"day": "Thursday", "focus": "Back & Biceps", "exercises": [{"name": "Lat Pulldowns", "sets": "3", "reps": "12", "tip": "Squeeze shoulder blades"}]},
                {"day": "Friday", "focus": "Shoulders", "exercises": [{"name": "Overhead Press", "sets": "3", "reps": "10", "tip": "Keep core tight"}]},
                {"day": "Saturday", "focus": "Cardio", "exercises": [{"name": "Treadmill Walk", "sets": "1", "reps": "20min", "tip": "Incline 3%"}]},
                {"day": "Sunday", "focus": "Rest", "exercises": []}
            ]
        }

def generate_home_workout(profile, mode='normal', focus=None, report_id=None):
    """
    Generate a professional Home-specific workout plan.
    Modes: 'normal' (maintenance), 'medical' (based on report issues)
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-flash-latest")

    report_context = ""
    report = None
    if mode == 'medical':
        if report_id:
            report = MedicalReport.objects.filter(user=profile.user, id=report_id).first()
        if not report:
            report = MedicalReport.objects.filter(user=profile.user).order_by('-uploaded_at').first()
        if report:
            report_context = f"LATEST MEDICAL REPORT FINDINGS: {report.conditions_notes}\nSUMMARY: {report.summary}"

    profile_data = f"""
    Age: {profile.age}, Gender: {profile.gender}, Weight: {profile.weight}kg, Activity: {profile.activity_level}, Sugar: {profile.sugar_status}
    """

    focus_text = f" Specifically focus on this goal: {focus}." if focus else ""
    if mode == 'medical':
        prompt_goal = f"HEALING & SAFETY AT HOME. Adapt activities to address risks found in its report using NO heavy equipment. Focus on bodyweight and safe stretches.{focus_text}"
    else:
        prompt_goal = f"HOME BODY MAINTENANCE & TARGETED GOALS. Focus on general fitness using bodyweight or minimal household items.{focus_text}"

    prompt = f"""
    Act as a professional Home Fitness Coach. Create a 7-day Home Workout Plan.
    MODE: {mode.upper()}
    GOAL: {prompt_goal}
    
    Profile: {profile_data}
    {report_context}
    
    The plan must NOT require heavy gym equipment. Focus on bodyweight, resistance bands, or household items.
    
    Provide output in JSON:
    {{
        "title": "{mode.capitalize()} Home Routine",
        "description": "7-day customized home routine for {mode} needs.",
        "days": [
            {{
                "day": "Monday",
                "focus": "...",
                "exercises": [
                    {{ "name": "...", "sets": "3", "reps": "12", "tip": "..." }}
                ]
            }},
            ...
        ]
    }}
    """

    try:
        response = model.generate_content(prompt)
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response.text)
        if match:
            return json.loads(match.group(1))
        
        match = re.search(r"\{[\s\S]*\}", response.text)
        if match:
            return json.loads(match.group(0))

        return {"error": "AI could not generate home plan."}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {
            "title": "Essential Home Routine (Free Mode)",
            "description": "Safe, effective bodyweight exercises you can do anywhere (AI is currently resting).",
            "days": [
                {"day": "Monday", "focus": "Full Body", "exercises": [{"name": "Bodyweight Squats", "sets": "3", "reps": "15", "tip": "Chest up"}]},
                {"day": "Tuesday", "focus": "Core", "exercises": [{"name": "Plank", "sets": "3", "reps": "45s", "tip": "Flat back"}]},
                {"day": "Wednesday", "focus": "Active Recovery", "exercises": [{"name": "Walking", "sets": "1", "reps": "20min", "tip": "Fresh air"}]},
                {"day": "Thursday", "focus": "Upper Body", "exercises": [{"name": "Pushups", "sets": "3", "reps": "Max", "tip": "Go to knees if needed"}]},
                {"day": "Friday", "focus": "Lower Body", "exercises": [{"name": "Lunges", "sets": "3", "reps": "10/leg", "tip": "Large steps"}]},
                {"day": "Saturday", "focus": "Full Body", "exercises": [{"name": "Burpees", "sets": "3", "reps": "10", "tip": "Pace yourself"}]},
                {"day": "Sunday", "focus": "Rest", "exercises": []}
            ]
        }

def generate_yoga_workout(profile, mode='normal', report_id=None):
    """
    Generate a professional Yoga & Mindfulness plan.
    Modes: 'normal' (flexibility/peace), 'medical' (therapy based on report)
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-flash-latest")

    report_context = ""
    latest_report = None
    if mode == 'medical':
        if report_id:
            latest_report = MedicalReport.objects.filter(user=profile.user, id=report_id).first()
        if not latest_report:
            latest_report = MedicalReport.objects.filter(user=profile.user).order_by('-uploaded_at').first()
        if latest_report:
            report_context = f"LATEST MEDICAL REPORT FINDINGS: {latest_report.conditions_notes}\nSUMMARY: {latest_report.summary}"

    profile_data = f"Age: {profile.age}, Gender: {profile.gender}, Weight: {profile.weight}kg, Sugar: {profile.sugar_status}"

    if mode == 'medical':
        prompt_goal = "THERAPEUTIC YOGA. Focus on poses that help with the conditions in the medical report (e.g., stress reduction for high BP, gentle movements for joint pain)."
    else:
        prompt_goal = "HOLISTIC WELLNESS. Focus on flexibility, balance, core strength, and mental peace."

    prompt = f"""
    Act as an expert Yoga Instructor (Yogi). Create a 7-day Yoga & Meditation Plan.
    MODE: {mode.upper()}
    GOAL: {prompt_goal}
    
    Profile: {profile_data}
    {report_context}
    
    The plan should include Asanas (poses), Pranayama (breathing), and Meditation.
    
    Provide output in JSON:
    {{
        "title": "{mode.capitalize()} Yoga Journey",
        "description": "7-day professional yoga and mindfulness guide.",
        "days": [
            {{
                "day": "Monday",
                "focus": "...",
                "poses": [
                    {{ "name": "...", "duration": "5 mins", "benefit": "..." }}
                ]
            }}
        ]
    }}
    Include all 7 days in the actual output.
    """

    try:
        response = model.generate_content(prompt)
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response.text)
        if match:
            return json.loads(match.group(1))
        
        match = re.search(r"\{[\s\S]*\}", response.text)
        if match:
            return json.loads(match.group(0))

        return {"error": "AI could not generate yoga plan."}
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {
            "title": "Foundation Yoga Flow (Free Mode)",
            "description": "A grounding yoga practice focusing on flexibility, balance, and breath (AI is resting).",
            "days": [
                {"day": "Monday", "focus": "Morning Energizer", "poses": [{"name": "Sun Salutation A", "duration": "-", "benefit": "Move with breath"}]},
                {"day": "Tuesday", "focus": "Hip Openers", "poses": [{"name": "Pigeon Pose", "duration": "2min/leg", "benefit": "Keep hips square"}]},
                {"day": "Wednesday", "focus": "Rest & Restore", "poses": [{"name": "Child's Pose", "duration": "5min", "benefit": "Relax shoulders"}]},
                {"day": "Thursday", "focus": "Core Strength", "poses": [{"name": "Boat Pose", "duration": "30sec", "benefit": "Lift the chest"}]},
                {"day": "Friday", "focus": "Backbends", "poses": [{"name": "Bridge Pose", "duration": "5 breaths", "benefit": "Press into heels"}]},
                {"day": "Saturday", "focus": "Balance", "poses": [{"name": "Tree Pose", "duration": "1min/leg", "benefit": "Find a focal point"}]},
                {"day": "Sunday", "focus": "Deep Relaxation", "poses": [{"name": "Savasana", "duration": "10min", "benefit": "Completely let go"}]}
            ]
        }
