import streamlit as st
import requests

# Backend URL (change to your deployed FastAPI endpoint)
API_URL = "http://localhost:8000/api/ask"

st.set_page_config(page_title="Clinical RAG Assistant", layout="centered")
st.title("🩺 Clinical Notes Assistant")

st.markdown("Ask questions based on uploaded clinical notes.")

# Input question
question = st.text_input("💬 Your question", placeholder="e.g., What medications was the patient prescribed?")

if st.button("Ask") and question:
    try:
        with st.spinner("Thinking..."):
            response = requests.post(API_URL, json={"question": question})
            response.raise_for_status()
            answer = response.json().get("answer", "No answer received.")
        st.success("✅ Answer:")
        st.markdown(f"**{answer}**")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API error: {e}")
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
