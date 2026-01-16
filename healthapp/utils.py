import google.generativeai as genai
from django.conf import settings


# --------------------------------------------------
# RULE-BASED + AI-POWERED HEALTH RECOMMENDATIONS
# --------------------------------------------------
def generate_recommendations(profile, bmi, score):
    # ---------------- RULE-BASED PART (UNCHANGED) ----------------
    recommendations = {
        "diet": [],
        "exercise": [],
        "lifestyle": []
    }

    # ---- BMI BASED ----
    if bmi < 18.5:
        recommendations["diet"].append(
            "Increase calorie intake with nutrient-rich foods like nuts, dairy, and whole grains."
        )
        recommendations["exercise"].append(
            "Focus on strength training to build muscle mass."
        )

    elif 18.5 <= bmi < 25:
        recommendations["diet"].append(
            "Maintain a balanced diet with fruits, vegetables, and lean proteins."
        )
        recommendations["exercise"].append(
            "Continue regular moderate exercise (30 minutes daily)."
        )

    else:
        recommendations["diet"].append(
            "Reduce sugar and refined carbohydrates; focus on fiber-rich foods."
        )
        recommendations["exercise"].append(
            "Include daily cardio such as walking, cycling, or swimming."
        )

    # ---- SUGAR LEVEL ----
    if profile.sugar_level > 140:
        recommendations["diet"].append(
            "Limit sugary foods and monitor carbohydrate intake closely."
        )

    # ---- ACTIVITY LEVEL ----
    if profile.activity_level == "Low":
        recommendations["exercise"].append(
            "Start with light activities like walking or stretching."
        )

    # ---- SLEEP ----
    if profile.sleep_hours < 6:
        recommendations["lifestyle"].append(
            "Aim for at least 7–8 hours of sleep to support metabolic health."
        )

    # ---- SMOKING & ALCOHOL ----
    if profile.smoker:
        recommendations["lifestyle"].append(
            "Consider reducing or quitting smoking to lower cardiovascular risk."
        )

    if profile.alcohol:
        recommendations["lifestyle"].append(
            "Limit alcohol consumption to improve liver and heart health."
        )

    # ---- HEALTH SCORE ----
    if score < 50:
        recommendations["lifestyle"].append(
            "Consult a healthcare professional for personalized medical advice."
        )

    # ---------------- AI PART (GOOGLE GEMINI) ----------------
    ai_text = "AI advice unavailable."

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)

        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
You are a professional medical health assistant.

User Profile:
Age: {profile.age}
Gender: {profile.gender}
BMI: {bmi}
Blood Sugar Level: {profile.sugar_level} mg/dL
Activity Level: {profile.activity_level}
Smoker: {profile.smoker}
Alcohol Consumption: {profile.alcohol}
Sleep Hours: {profile.sleep_hours}
Health Score: {score}/100

Provide:
1. Overall health assessment in bullet points
2. Detailed diet advice in bullet points
3. Exercise recommendations in bullet points
4. Lifestyle improvements in bullet points
5. Health warnings (if any) in bullet points

Use simple, safe, non-alarming language.
"""

        response = model.generate_content(prompt)
        ai_text = response.text

    except Exception as e:
        ai_text = f"AI error: {str(e)}"


    # ---------------- FINAL COMBINED OUTPUT ----------------
    return {
        "rule_based": recommendations,
        "ai_based": ai_text
    }
