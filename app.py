import streamlit as st
import pypdf
import os
from dotenv import load_dotenv
from google import genai
from pathlib import Path

# --- 1. UI SETUP & CSS ---
st.set_page_config(page_title="Legalize AI", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    
    /* Hide Streamlit default footer/menu and your GitHub badge */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;} 

    /* Chatbot Box Styling */
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
        border-top: 5px solid #007bff;
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. INITIALIZATION ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or "YOUR_API_KEY_HERE"
client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

# Navigation & State Control
if "current_page" not in st.session_state:
    st.session_state.current_page = "upload"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""

def extract_text(pdf_file):
    reader = pypdf.PdfReader(pdf_file)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

# --- 3. TOP NAVIGATION BAR (Language at Top Right) ---
# We create two columns: one for the title/spacer, and a small one at the right for language
nav_left, nav_right = st.columns([8, 2])

with nav_right:
    target_language = st.selectbox(
        "🌐 Language",
        ["English", "French", "Spanish", "Portuguese", "Chinese", "Korean", "Tagalog", "Indonesian"],
        index=0
    )

# --- 4. PAGE 1: UPLOAD & ANALYZE ---
if st.session_state.current_page == "upload":
    st.title("⚖️ Legalize AI: Smart Contract Auditor")
    st.subheader("Step 1: Upload Your Document 📝")
    
    uploaded_file = st.file_uploader("Upload Contract (PDF)", type="pdf")
    
    if uploaded_file:
        if st.button("🚀 Analyze Contract Now"):
            with st.status("🔍 Processing document...", expanded=True) as status:
                raw_text = extract_text(uploaded_file)
                st.session_state.contract_text = raw_text
                
                # Prompt with Strict Language Requirement
                prompt = f"""
                Act as a casual, friendly legal expert. Explain this contract using LOTS of emojis.
                Break it down like I'm 15 years old.
                
                IMPORTANT: You MUST provide the entire response in {target_language}.
                
                Structure:
                - 🛡️ SAFETY SCORE (1 to 10)
                - 🚩 RED FLAGS (Sneaky stuff)
                - 💡 SUMMARY (What is this actually?)
                - ✅ VERDICT (Sign or Run?)
                
                Text Content: {raw_text[:10000]}
                """
                
                try:
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    st.session_state.analysis_result = response.text
                    status.update(label="✅ Analysis Finished!", state="complete")
                except Exception as e:
                    st.error(f"AI Error: {e}")

    if st.session_state.analysis_result:
        st.success(f"Analysis complete in {target_language}!")
        if st.button("➡️ View Full Audit Report"):
            st.session_state.current_page = "results"
            st.rerun()

# --- 5. PAGE 2: RESULTS & CHATBOT ---
elif st.session_state.current_page == "results":
    col_head, col_back = st.columns([8, 2])
    with col_head:
        st.title(f"⚖️ Results ({target_language})")
    with col_back:
        if st.button("🏠 New Upload"):
            st.session_state.current_page = "upload"
            st.session_state.analysis_result = ""
            st.session_state.messages = []
            st.rerun()

    left_col, right_col = st.columns([1.5, 1], gap="large")

    with left_col:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("📊 Document Analysis Report")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        st.subheader(f"💬 Chat Assistant")
        
        chat_display = st.container(height=400)
        with chat_display:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        if query := st.chat_input(f"Ask in {target_language}..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with chat_display:
                with st.chat_message("user"):
                    st.markdown(query)
                
                with st.chat_message("assistant"):
                    ctx = st.session_state.contract_text
                    full_p = f"Based on this text: {ctx[:8000]}\nAnswer this question in {target_language}: {query}"
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=full_p)
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. GLOBAL FOOTER ---
st.markdown(f"""
    <div class="disclaimer-box">
        ⚠️ <b>Disclaimer:</b> I am AI, I provide answers based on provided data which may not reflect real-world legal scenarios. 
        This tool is for educational purposes only and does not substitute for professional legal advice.
    </div>
    """, unsafe_allow_html=True)
