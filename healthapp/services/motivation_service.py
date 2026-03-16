import google.generativeai as genai
from django.conf import settings
import random

def get_daily_motivation(user, streak=0):
    """
    Generate a fresh motivational quote using AI or fallback.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-flash-latest")
        
        prompt = f"Generate a unique, powerful one-line motivational quote for a person using a health app. Their current streak is {streak} days. Make it punchy, short, and extremely inspiring. Focus on consistency and power. No tags or explanations, just the quote."
        
        response = model.generate_content(prompt)
        quote = response.text.strip().replace('"', '')
        if len(quote) < 10 or len(quote) > 150: # Sanity check
             raise ValueError("Quote length outlier")
        return quote
    except Exception as e:
        print(f"Motivation AI Error: {e}")
        fallbacks = [
            "The only bad workout is the one that didn't happen.",
            "Your body can stand almost anything. It’s your mind that you have to convince.",
            "Fitness is not about being better than someone else. It’s about being better than you were yesterday.",
            "Take care of your body. It's the only place you have to live.",
            "Small steps every day lead to big results.",
            "Your health is an investment, not an expense."
        ]
        return random.choice(fallbacks)
