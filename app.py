import streamlit as st
import PyPDF2
import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv

# -----------------------------
# 🔐 Secure API Key Handling
# -----------------------------
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except:
    load_dotenv()
    API_KEY = os.getenv("OPENROUTER_API_KEY")

# -----------------------------
# 🎯 UI
# -----------------------------
st.set_page_config(page_title="AI Resume Job Matcher", layout="centered")
st.title("🚀 AI Resume Job Matcher")
st.write("Upload your resume and paste job description")

# -----------------------------
# 📄 Extract text from PDF
# -----------------------------
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# -----------------------------
# 📥 Inputs
# -----------------------------
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
job_description = st.text_area("Paste Job Description")

# -----------------------------
# 🚀 Analyze
# -----------------------------
if st.button("Analyze Resume"):

    if uploaded_file and job_description:

        resume_text = extract_text_from_pdf(uploaded_file)

        prompt = f"""
Compare the resume with the job description.

Return ONLY JSON:

{{
  "score": integer between 0 and 100,
  "matching_skills": [],
  "missing_skills": [],
  "suggestions": []
}}

Resume:
{resume_text}

Job Description:
{job_description}
"""

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openrouter/auto",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        with st.spinner("Analyzing..."):
            response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]

            try:
                start = result.find("{")
                end = result.rfind("}") + 1
                data = json.loads(result[start:end])

                score = data.get("score", 0)
                if isinstance(score, float):
                    score = int(score * 100)
                else:
                    score = int(score)

                matching = data.get("matching_skills", [])
                missing = data.get("missing_skills", [])
                suggestions = data.get("suggestions", [])

                # UI
                st.subheader("📊 Resume Score")
                st.progress(score / 100)
                st.write(f"Score: {score}/100")

                st.subheader("✅ Matching Skills")
                st.write(", ".join(matching) if matching else "None")

                st.subheader("❌ Missing Skills")
                st.write(", ".join(missing) if missing else "None")

                st.subheader("💡 Suggestions")
                for s in suggestions:
                    st.write(f"- {s}")

                chart_data = pd.DataFrame({
                    "Category": ["Matching", "Missing"],
                    "Count": [len(matching), len(missing)]
                })

                st.subheader("📈 Skills Overview")
                st.bar_chart(chart_data.set_index("Category"))

            except:
                st.error("⚠️ Parsing failed")
                st.write(result)

        else:
            st.error("❌ API Error")
            st.write(response.text)

    else:
        st.warning("⚠️ Upload resume and enter job description")