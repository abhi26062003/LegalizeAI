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

# --- 3. PAGE 1: UPLOAD & ANALYZE ---
if st.session_state.current_page == "upload":
    st.title("⚖️ Legalize AI: Smart Contract Auditor")
    st.subheader("Step 1: Upload Your Document 📝")
    
    uploaded_file = st.file_uploader("Upload Contract (PDF)", type="pdf")
    
    if uploaded_file:
        if st.button("🚀 Analyze Contract Now"):
            with st.status("🔍 Processing document...", expanded=True) as status:
                raw_text = extract_text(uploaded_file)
                st.session_state.contract_text = raw_text
                
                # Prompt with Strict Emoji requirement
                prompt = f"""
                Act as a casual, friendly legal expert. Explain this contract using LOTS of emojis.
                Break it down like I'm 15 years old.
                
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

    # Show navigation button ONLY if analysis is done
    if st.session_state.analysis_result:
        st.success("Analysis complete! Click below to see the results.")
        if st.button("➡️ View Full Audit Report"):
            st.session_state.current_page = "results"
            st.rerun()

# --- 4. PAGE 2: RESULTS & CHATBOT ---
elif st.session_state.current_page == "results":
    col_head, col_back = st.columns([8, 2])
    with col_head:
        st.title("⚖️ Audit Results & AI Assistant")
    with col_back:
        if st.button("🏠 New Upload"):
            st.session_state.current_page = "upload"
            st.session_state.analysis_result = ""
            st.session_state.messages = []
            st.rerun()

    # Split Screen: Left (Report) | Right (Chatbot)
    left_col, right_col = st.columns([1.5, 1], gap="large")

    with left_col:
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("📊 Document Analysis Report")
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="chat-box">', unsafe_allow_html=True)
        st.subheader("💬 Chat with Document")
        
        # Chat Display
        chat_display = st.container(height=400)
        with chat_display:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

        # Chat Input inside the right-side area
        if query := st.chat_input("Ask a specific question..."):
            st.session_state.messages.append({"role": "user", "content": query})
            with chat_display:
                with st.chat_message("user"):
                    st.markdown(query)
                
                with st.chat_message("assistant"):
                    ctx = st.session_state.contract_text
                    full_p = f"Based on this text: {ctx[:8000]}\nAnswer this: {query}"
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=full_p)
                    st.markdown(res.text)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. GLOBAL FOOTER ---
st.markdown(f"""
    <div class="disclaimer-box">
        ⚠️ <b>Disclaimer:</b> I am Ai, i want giving you answer based on provided data and it does not authentic with your real world senerio. 
        This tool is for educational purposes only and does not substitute for real-world legal advice.
    </div>
    """, unsafe_allow_html=True)
