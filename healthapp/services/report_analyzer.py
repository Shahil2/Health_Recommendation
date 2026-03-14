"""Extract content from medical reports (PDF/images) and analyze via Gemini."""
import google.generativeai as genai
from django.conf import settings
import os
import json
import re


def _extract_text_from_pdf(file_path):
    """Extract text from PDF using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def _get_file_extension(file_path):
    return os.path.splitext(file_path)[1].lower()


def extract_report_content(file_path):
    """Extract text from PDF or return path for image (Gemini vision handles images)."""
    ext = _get_file_extension(file_path)
    if ext == ".pdf":
        return _extract_text_from_pdf(file_path), "text"
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        return file_path, "image"
    return None, None


def _parse_json_array(text):
    """Extract JSON array from text (handles ```json ... ``` blocks)."""
    match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return []


def _parse_metrics_json(text):
    """Alias for backward compatibility."""
    return _parse_json_array(text)


def _normalize_plans(arr, plan_type):
    """Ensure list fields (items, activities, foods, avoid) are always lists."""
    if not isinstance(arr, list):
        return []
    result = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        copy = dict(item)
        if plan_type == "lifestyle_plan" and "items" in copy:
            copy["items"] = copy["items"] if isinstance(copy["items"], list) else [str(copy["items"])]
        if plan_type == "workout_plan" and "activities" in copy:
            copy["activities"] = copy["activities"] if isinstance(copy["activities"], list) else [str(copy["activities"])]
        if plan_type == "diet_plan":
            if "foods" in copy:
                copy["foods"] = copy["foods"] if isinstance(copy["foods"], list) else [str(copy["foods"])]
            if "avoid" in copy:
                copy["avoid"] = copy["avoid"] if isinstance(copy["avoid"], list) else [str(copy["avoid"])]
        result.append(copy)
    return result


def analyze_medical_report(file_path, extracted_text=None, is_image=False):
    """
    Analyze medical report via Gemini.
    Returns dict with: summary, lifestyle_advice, medicine_suggestions, doctor_suggestions,
    conditions_notes, extracted_metrics (list of {name, value, unit, status, normal_range})
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("models/gemini-flash-latest")

    prompt = """
You are a friendly health assistant. Analyze this medical report.

**MULTI-LANGUAGE**: The report may be in ANY language (English, Hindi, Tamil, Telugu, Malayalam, Arabic, Spanish, etc.).
- Read and understand the report in its original language.
- Respond in the SAME language as the report. If the report is in multiple languages, use the main language.
- Keep all output simple and easy to understand.

**FORMAT**: NO long paragraphs. Use ONLY structured JSON and short bullet lists. Everything must be easy to scan visually.

**IMPORTANT**: This is NOT a medical diagnosis. User must consult a doctor. Do NOT prescribe specific drugs.

---

**1. EXTRACT HEALTH METRICS** (from the report - BMI, BP, sugar, cholesterol, etc.):
---METRICS_JSON---
```json
[{"name":"BMI","value":24.5,"unit":"kg/m²","status":"Normal","normal_range":"18.5-25"},{"name":"Blood Pressure","value":"120/80","unit":"mmHg","status":"Normal","normal_range":"Below 120/80"}]
```
Use actual values from report. Empty [] if none found.

---

**2. SUMMARY** (1-2 short sentences, same language as report):
---SUMMARY---
[What does this report say? Main takeaway.]

---

**3. LIFESTYLE PLAN** (to overcome health issues - structured, NOT paragraphs):
---LIFESTYLE_PLAN_JSON---
```json
[
  {"category":"Sleep","items":["7-8 hours daily","Same bedtime each night","No screens 1hr before bed"]},
  {"category":"Stress","items":["15 min meditation","Take short breaks","Avoid overwork"]},
  {"category":"Habits","items":["Quit smoking","Limit alcohol","Stay active"]}
]
```
Create 3-5 categories (Sleep, Stress, Diet habits, Activity, Hydration, etc.) with 2-4 short items each. Based on report findings.

---

**4. WORKOUT PLAN** (specific exercises, NOT paragraphs):
---WORKOUT_PLAN_JSON---
```json
[
  {"type":"Cardio","activities":["30 min brisk walk","or 15 min jog"],"duration":"30 min","frequency":"5 days/week"},
  {"type":"Strength","activities":["Squats 10x3","Push-ups 10x2","Plank 30 sec"],"duration":"15-20 min","frequency":"3 days/week"},
  {"type":"Flexibility","activities":["Stretching","Yoga basics"],"duration":"10 min","frequency":"Daily"}
]
```
Adapt to report (e.g. if knee issues, suggest low-impact). Keep each activity short (one line).

---

**5. DIET PLAN** (meal-wise, NOT paragraphs):
---DIET_PLAN_JSON---
```json
[
  {"meal":"Breakfast","foods":["Oats","Eggs","Fruits"],"avoid":["Sugary cereals","Fried"],"tips":"Eat within 1hr of waking"},
  {"meal":"Lunch","foods":["Rice/Roti","Dal","Vegetables","Salad"],"avoid":["White bread","Excess oil"],"tips":"Half plate vegetables"},
  {"meal":"Dinner","foods":["Light meal","Soup","Vegetables"],"avoid":["Heavy food","Late eating"],"tips":"2-3 hrs before sleep"},
  {"meal":"Snacks","foods":["Nuts","Fruit","Curd"],"avoid":["Chips","Sweets"]}
]
```
Adapt to report (diabetes=sugar control, BP=salt limit, etc.). Use local foods if report language suggests regional diet.

---

**6. MEDICINE TIPS** (general types only, 2-4 short bullets):
---MEDICINE_SUGGESTIONS---
• [Type 1 - e.g. "Vitamins if deficient"]
• [Type 2]
• Always ask your doctor before taking any medicine.

---

**7. DOCTOR SUGGESTIONS** (who to see, 2-4 short bullets):
---DOCTOR_SUGGESTIONS---
• [Specialist - e.g. "Heart doctor (Cardiologist) if BP high"]
• [What to ask]
• [When to follow up]

---

**8. KEY FINDINGS** (conditions/risks, 3-5 short bullets):
---CONDITIONS_NOTES---
• [Finding 1]
• [Finding 2]
• Normal vs not normal. Simple words.
"""

    try:
        if is_image and file_path and os.path.exists(file_path):
            from PIL import Image
            img = Image.open(file_path)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            response = model.generate_content([prompt, img])
        else:
            text = extracted_text or ""
            if not text.strip():
                return {
                    "summary": "Could not read the report.",
                    "lifestyle_advice": "Please upload a clear PDF or image.",
                    "medicine_suggestions": "Consult a doctor with your report.",
                    "doctor_suggestions": "Visit a general physician.",
                    "conditions_notes": "Unable to analyze.",
                    "extracted_metrics": [],
                    "lifestyle_plan": [],
                    "workout_plan": [],
                    "diet_plan": [],
                }
            response = model.generate_content(prompt + "\n\n---REPORT CONTENT---\n" + text)

        raw = response.text.strip()

        # Parse sections
        sections = {
            "summary": "",
            "lifestyle_advice": "",
            "medicine_suggestions": "",
            "doctor_suggestions": "",
            "conditions_notes": "",
            "extracted_metrics": [],
            "lifestyle_plan": [],
            "workout_plan": [],
            "diet_plan": [],
        }
        json_sections = {"metrics_json": "extracted_metrics", "lifestyle_plan_json": "lifestyle_plan",
                        "workout_plan_json": "workout_plan", "diet_plan_json": "diet_plan"}
        current = None
        buf = []
        for line in raw.split("\n"):
            if line.strip().startswith("---") and line.strip().endswith("---"):
                if current:
                    val = "\n".join(buf).strip()
                    if current in json_sections:
                        arr = _parse_json_array(val) if val else []
                        if json_sections[current] in ("lifestyle_plan", "workout_plan", "diet_plan"):
                            arr = _normalize_plans(arr, json_sections[current])
                        sections[json_sections[current]] = arr
                    elif current in sections:
                        sections[current] = val
                raw_name = line.strip().strip("-").strip().lower().replace(" ", "_").replace("-", "_")
                if raw_name in json_sections:
                    current = raw_name
                elif raw_name in sections:
                    current = raw_name
                else:
                    current = raw_name
                buf = []
            elif current:
                buf.append(line)
        if current:
            val = "\n".join(buf).strip()
            if current in json_sections:
                arr = _parse_json_array(val) if val else []
                if json_sections[current] in ("lifestyle_plan", "workout_plan", "diet_plan"):
                    arr = _normalize_plans(arr, json_sections[current])
                sections[json_sections[current]] = arr
            elif current in sections:
                sections[current] = val

        return sections
    except Exception as e:
        return {
            "summary": f"Something went wrong: {str(e)}",
            "lifestyle_advice": "Please consult a doctor with your report.",
            "medicine_suggestions": "",
            "doctor_suggestions": "",
            "conditions_notes": "",
            "extracted_metrics": [],
            "lifestyle_plan": [],
            "workout_plan": [],
            "diet_plan": [],
        }
