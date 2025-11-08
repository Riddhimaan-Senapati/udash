import streamlit as st
import requests

st.title("🤖 Agentic Order Assistant")

API_URL = "http://localhost:8002/chat"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for user configuration and instructions
with st.sidebar:
    st.markdown("### User Configuration")
    user_id = st.text_input(
        "User UUID",
        value="10fccccb-4f6c-4a8f-954f-1d88aafeaa37",
        help="Enter your user UUID from Supabase profiles table"
    )

    st.markdown("### Setup")
    st.markdown("1. Start orders API: `python backend/orders_api.py`")
    st.markdown("2. Start chatbot: `python backend/chatbot_api.py`")
    st.markdown("3. Set GOOGLE_API_KEY in backend/.env")
    st.markdown("### Try asking:")
    st.markdown("- Show me breakfast items from Worcester")
    st.markdown("- What food has the most protein?")
    st.markdown("- Create an order with French Toast Sticks")
    st.markdown("- Show me my orders")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about orders..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = requests.post(API_URL, json={
                "message": prompt,
                "user_id": user_id
            })
            if response.status_code == 200:
                bot_response = response.json()["response"]
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Could not connect to API. Ensure both servers are running. Error: {e}")
