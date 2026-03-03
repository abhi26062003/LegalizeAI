import streamlit as st
import pypdf
import os
import io
from dotenv import load_dotenv
from google import genai
from pathlib import Path

# --- 1. UI SETUP & CSS ---
st.set_page_config(page_title="Legalize AI Pro", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;} 

    .chat-box {
        border: 2px solid #007bff;
        border-radius: 15px;
        background-color: #ffffff;
        padding: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .report-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-top: 8px solid #007bff;
    }
    .disclaimer-box {
        font-size: 13px;
        color: #555;
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        text-align: center;
        border: 1px solid #ffeeba;
        margin-top: 30px;
    }
    .metric-card {
        background-color: #e9ecef;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or "YOUR_API_KEY_HERE"
client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

if "current_page" not in st.session_state: st.session_state.current_page = "upload"
if "analysis_result" not in st.session_state: st.session_state.analysis_result = ""
if "messages" not in st.session_state: st.session_state.messages = []
if "contract_text" not in st.session_state: st.session_state.contract_text = ""
if "safety_score" not in st.session_state: st.session_state.safety_score = 5

def extract_text(pdf_file):
    reader = pypdf.PdfReader(pdf_file)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

# --- 3. TOP NAVIGATION ---
nav_left, nav_right = st.columns([8, 2])
with nav_right:
    target_language = st.selectbox(
        "🌐 Language",
        ["English", "French", "Spanish", "Portuguese", "Chinese", "Korean", "Tagalog", "Indonesian"],
        index=0
    )

# --- 4. PAGE 1: UPLOAD & ANALYZE ---
if st.session_state.current_page == "upload":
    st.title("⚖️ Legalize AI: Professional Auditor")
    st.subheader("Fast, Ethical, and Transparent Contract Auditing 📝")
    
    uploaded_file = st.file_uploader("Drop your PDF contract here", type="pdf")
    
    if uploaded_file:
        if st.button("🚀 Run Full AI Audit"):
            with st.status("🧠 Extracting Legal Logic...", expanded=True) as status:
                raw_text = extract_text(uploaded_file)
                st.session_state.contract_text = raw_text
                
                prompt = f"""
                Act as a world-class legal auditor. Analyze this contract and respond ONLY in {target_language}.
                Use clear emojis and professional-yet-simple language.
                
                STRUCTURE:
                1. 🛡️ SAFETY SCORE: Provide only a number from 1 to 10.
                2. 📝 TL;DR: A 2-sentence executive summary.
                3. 🚩 RED FLAGS: Bullet points of sneaky or unfair clauses.
                4. 💡 DETAILED SUMMARY: Break down the core obligations.
                5. ✅ VERDICT: Final recommendation.
                
                Content: {raw_text[:12000]}
                """
                
                try:
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    st.session_state.analysis_result = response.text
                    
                    # Logic to extract score for the gauge
                    import re
                    score_match = re.search(r'SAFETY SCORE:?\s*(\d+)', response.text)
                    if score_match:
                        st.session_state.safety_score = int(score_match.group(1))
                    
                    status.update(label="✅ Audit Complete!", state="complete")
                except Exception as e:
                    st.error(f"AI Connection Failed: {e}")

    if st.session_state.analysis_result:
        st.success(f"Audit report generated in {target_language}!")
        if st.button("➡️ Enter Audit Dashboard"):
            st.session_state.current_page = "results"
            st.rerun()

# --- 5. PAGE 2: DASHBOARD ---
elif st.session_state.current_page == "results":
    col_h, col_b = st.columns([8, 2])
    with col_h:
        st.title(f"📊 Legal Dashboard ({target_language})")
    with col_b:
        if st.button("🏠 New Audit"):
            st.session_state.current_page = "upload"
            st.session_state.analysis_result = ""
            st.session_state.messages = []
            st.rerun()

    # Visual Insights Row
    row1_1, row1_2, row1_3 = st.columns(3)
    with row1_1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Safety Rating", f"{st.session_state.safety_score}/10")
        st.progress(st.session_state.safety_score / 10)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with row1_2:
        st.download_button("📥 Download Audit (.txt)", st.session_state.analysis_result, file_name="Legalize_AI_Report.txt")

    # Main Dashboard
    left_col, right_col = st.columns([1.5, 1], gap="large")

    with left_col:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("🧐 Casual Audit Report")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        st.subheader("💬 Clause Query Assistant")
        chat_display = st.container(height=450)
        with chat_display:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        if query := st.chat_input(f"Question about the {target_language} clauses?"):
            st.session_state.messages.append({"role": "user", "content": query})
            with chat_display:
                with st.chat_message("user"): st.markdown(query)
                with st.chat_message("assistant"):
                    ctx = st.session_state.contract_text
                    full_p = f"Ref text: {ctx[:9000]}\nReply in {target_language}: {query}"
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=full_p)
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. FOOTER ---
st.markdown(f"""
    <div class="disclaimer-box">
        ⚠️ <b>Ethical AI Warning:</b> This tool provides probabilistic analysis based on provided data. 
        It is intended for educational and preliminary screening purposes and does NOT constitute legal advice.
    </div>
    """, unsafe_allow_html=True)
