# 🧠 Smart Health – AI Powered Health Profile Analyzer

**Smart Health** is an advanced AI-integrated healthcare application designed to provide personalized health insights. By combining medical vitals analysis with Google's Gemini LLM, it offers a holistic view of your well-being.

---

## 🚀 Key Features
- **🩺 Health Score Analysis**: Instant 0–100 score based on BMI, BP, Sugar, and habits.
- **📄 AI Medical Report Decoder**: Upload reports (PDF/Image) for an easy-to-understand AI summary.
- **🥗 Personalized Health Plans**: AI-generated diet and workout routines tailored to your vitals.
- **📈 Activity Dashboard**: Track your daily streaks and health trends.
- **🌙 Modern UI**: Premium dark-mode dashboard with glassmorphism aesthetics.

## 🛠 Tech Stack
- **Backend**: Django (Python) 🐍
- **AI**: Google Gemini API (LLM & Vision) ✨
- **Database**: SQLite 🗄️
- **Frontend**: Django Templates + CSS + JS 🎨

## 📥 Quick Start
1. **Configure Environment**:
   Add your `GEMINI_API_KEY` to a `.env` file.
2. **Install Dependencies**:
   `pip install -r requirements.txt` (or manually install django, python-dotenv, google-generativeai)
3. **Run App**:
   `python manage.py migrate`
   `python manage.py runserver`

## 📄 Documentation
For detailed technical info, architecture, and schema details, see [DOCUMENTATION.md](./DOCUMENTATION.md).

---
*Disclaimer: This application is for informational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment.*
