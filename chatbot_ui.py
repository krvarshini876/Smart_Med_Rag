import streamlit as st
from advanced_module import generate_results

st.set_page_config(page_title="SmartMed AI Chatbot", layout="wide")

st.title("🤖 SmartMed AI Chatbot")
st.subheader("Describe your symptoms naturally")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User Input
user_input = st.chat_input("Describe how you feel...")

if user_input:
    # Show user msg
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Run YOUR medical backend
    try:
        response = generate_results(user_input)
    except Exception as e:
        response = f"Error in diagnosis system: {str(e)}"

    # Show bot reply
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()