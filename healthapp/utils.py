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
You are a professional, ethical AI medical health assistant.

Analyze the following user health profile and provide clear, practical, and non-alarming guidance.
Do NOT diagnose diseases or prescribe medication.

USER HEALTH PROFILE:
- Age: {profile.age}
- Gender: {profile.gender}
- BMI: {bmi}
- Blood Sugar Level: {profile.sugar_level} mg/dL
- Activity Level: {profile.activity_level}
- Smoker: {profile.smoker}
- Alcohol Consumption: {profile.alcohol}
- Sleep Duration: {profile.sleep_hours} hours/night
- Overall Health Score: {score}/100

INSTRUCTIONS:
- Use simple, easy-to-understand language
- Be encouraging and supportive
- Avoid fear-based or extreme wording
- Provide actionable advice suitable for daily life
- Focus more on lifestyle improvement strategies

OUTPUT FORMAT (STRICTLY FOLLOW THIS STRUCTURE):

### 🩺 Overall Health Assessment
- (3–5 short bullet points summarizing current health status)

### 🥗 Diet Recommendations
- (5–7 bullet points with practical food choices and habits)

### 🏃 Exercise Recommendations
- (4–6 bullet points based on activity level and BMI)

### 🌱 Lifestyle Improvements (DETAILED)
- (6–8 bullet points focusing on:
  - sleep quality
  - stress management
  - screen time
  - daily routines
  - hydration
  - smoking/alcohol reduction strategies
  - mental well-being
)

### ⚠️ Health Cautions (If Applicable)
- (Only include if needed, keep calm and informative)

End with one short motivational sentence.

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
