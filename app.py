import streamlit as st
from llm import chat_once
from mistralai.models.chat_completion import ChatMessage

st.set_page_config(page_title="Simple Chatbot", layout="centered")
st.title("Scooby Chatbot")

# ---------------------------
# Session Storage
# ---------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
    # { chat_id: [ChatMessage, ...] }

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None


# ---------------------------
# Sidebar - Chat Management
# ---------------------------
st.sidebar.title("Chats")

# ➕ New Chat
if st.sidebar.button("➕ New Chat"):
    chat_id = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[chat_id] = []
    st.session_state.current_chat = chat_id

# Show existing chats
for chat_id in list(st.session_state.chats.keys()):
    col1, col2 = st.sidebar.columns([3, 1])

    if col1.button(chat_id, key=f"open_{chat_id}"):
        st.session_state.current_chat = chat_id

    if col2.button("❌", key=f"delete_{chat_id}"):
        del st.session_state.chats[chat_id]

        if st.session_state.current_chat == chat_id:
            st.session_state.current_chat = None

        st.rerun()


# ---------------------------
# Chat Area
# ---------------------------
if st.session_state.current_chat:
    st.subheader(f"Current: {st.session_state.current_chat}")

    chat_history = st.session_state.chats[st.session_state.current_chat]

    # Display messages
    for msg in chat_history:
        if msg.role == "user":
            st.write(f"**You:** {msg.content}")
        else:
            st.write(f"**Bot:** {msg.content}")

else:
    st.info("Start typing below — a new chat will be created automatically")


# ---------------------------
# Input Box
# ---------------------------
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:")
    submitted = st.form_submit_button("Send")


# ---------------------------
# Handle Input
# ---------------------------
if submitted and user_input.strip():

    # Auto-create chat if none exists
    if not st.session_state.current_chat:
        chat_id = f"Chat {len(st.session_state.chats) + 1}"
        st.session_state.chats[chat_id] = []
        st.session_state.current_chat = chat_id

    chat_messages = st.session_state.chats[st.session_state.current_chat]

    # Add user message
    chat_messages.append(
        ChatMessage(role="user", content=user_input)
    )

    # Get model response
    bot_reply = chat_once(chat_messages)

    # Add assistant message
    chat_messages.append(
        ChatMessage(role="assistant", content=bot_reply)
    )

    st.rerun()

elif submitted:
    st.warning("Enter something")