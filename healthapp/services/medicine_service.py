import google.generativeai as genai
from django.conf import settings
import os
import json
from PIL import Image

def analyze_medicine(medicine_name=None, image_path=None):
    """
    Analyze medicine using Gemini. 
    Accepts a name or an image file path.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    print("DEBUG: Initializing model models/gemini-flash-latest for medicine analyzer")
    model = genai.GenerativeModel("models/gemini-flash-latest")

    prompt = """
    You are a professional medical assistant. Analyze the following medicine (either by name or photo).
    
    Provide details in the following JSON format:
    {
        "name": "Corrected Medicine Name",
        "uses": ["Use 1", "Use 2"],
        "side_effects": ["Side effect 1", "Side effect 2"],
        "precautions": ["Precaution 1", "Precaution 2"],
        "dosage_info": "General dosage guidance (remind user to ask doctor)",
        "composition": "Chemical components if known"
    }
    
    IMPORTANT: 
    - Always include a disclaimer that this is not a prescription.
    - If it's a photo, identify the medicine accurately.
    - If you are not sure, say "Could not identify accurately".
    - Respond in simple, clear language.
    """

    try:
        if image_path and os.path.exists(image_path):
            with Image.open(image_path) as img:
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                response = model.generate_content([prompt, img])
        elif medicine_name:
            response = model.generate_content(prompt + f"\n\nMedicine Name: {medicine_name}")
        else:
            return {"error": "No medicine name or image provided."}

        # Extract JSON from response
        import re
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", response.text)
        if match:
            return json.loads(match.group(1))
        
        match = re.search(r"\{[\s\S]*\}", response.text)
        if match:
            return json.loads(match.group(0))

        return {"error": "Could not parse AI response."}

    except Exception as e:
        return {"error": str(e)}
