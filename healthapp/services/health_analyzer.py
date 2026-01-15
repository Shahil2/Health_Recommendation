import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GEMINI_API_KEY)


def generate_recommendations(profile, bmi, score):
    print("DEBUG: generate_recommendations() CALLED")

    rule_based = {
        "diet": [],
        "exercise": [],
        "lifestyle": []
    }

    # -------- RULE BASED --------
    if bmi < 18.5:
        rule_based["diet"].append("Increase calorie intake with healthy foods.")
        rule_based["exercise"].append("Light strength training.")
    elif bmi < 25:
        rule_based["diet"].append("Maintain a balanced diet.")
        rule_based["exercise"].append("30 minutes of daily exercise.")
    else:
        rule_based["diet"].append("Reduce sugar and refined carbs.")
        rule_based["exercise"].append("Daily cardio activities.")

    if profile.sleep_hours < 6:
        rule_based["lifestyle"].append("Improve sleep to 7–8 hours.")

    if profile.smoker:
        rule_based["lifestyle"].append("Quit smoking to reduce health risks.")

    if profile.alcohol:
        rule_based["lifestyle"].append("Reduce alcohol consumption.")

    # -------- AI PART --------
    ai_text = "AI advice unavailable."

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        response = model.generate_content(
            f"""
You are a friendly AI health assistant.

Age: {profile.age}
Gender: {profile.gender}
BMI: {bmi}
Blood Sugar Level: {profile.sugar_level}
Activity Level: {profile.activity_level}
Smoker: {profile.smoker}
Alcohol: {profile.alcohol}
Sleep Hours: {profile.sleep_hours}
Health Score: {score}/100

Give short, safe, and practical advice.
"""
        )

        ai_text = response.text.strip()

    except Exception as e:
        ai_text = f"AI ERROR: {e}"
        print("AI ERROR:", e)

    return {
        "rule_based": rule_based,
        "ai_based": ai_text
    }
