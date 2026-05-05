import streamlit as st
from llm import chat_once, extract_pdf_text
from mistralai.models.chat_completion import ChatMessage
import hashlib

st.set_page_config(page_title="Simple Chatbot", layout="centered")
st.title("Scooby Chatbot")

# ---------------------------
# 🔥 UI FIX (clean container + alignment)
# ---------------------------
st.markdown("""
<style>

/* Chat bubbles */
.user-msg {
    text-align: right;
    background: #2b2b2b;
    padding: 12px;
    border-radius: 12px;
    margin: 5px 0;
}
.bot-msg {
    text-align: left;
    background: #1e1e1e;
    padding: 12px;
    border-radius: 12px;
    margin: 5px 0;
}

/* Input container */
.input-box {
    border: 1px solid #2f2f2f;
    border-radius: 14px;
    padding: 12px;
    background-color: #111;
    margin-top: 20px;
}

/* Align row */
div[data-testid="stHorizontalBlock"] {
    align-items: center;
}

/* Input height */
input {
    height: 44px !important;
}

/* Send button */
button[kind="secondary"] {
    height: 44px !important;
}

/* Upload fix */
div[data-testid="stFileUploader"] {
    margin-top: -2px;
}

/* Remove label + padding */
div[data-testid="stFileUploader"] label {
    display: none;
}
div[data-testid="stFileUploader"] > div {
    padding: 0px !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# Session Storage
# ---------------------------
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "chat_files" not in st.session_state:
    st.session_state.chat_files = {}

if "upload_counter" not in st.session_state:
    st.session_state.upload_counter = {}

# ---------------------------
# Ensure chat exists
# ---------------------------
if not st.session_state.current_chat:
    chat_id = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[chat_id] = []
    st.session_state.chat_files[chat_id] = None
    st.session_state.upload_counter[chat_id] = 0
    st.session_state.current_chat = chat_id

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("Chats")

if st.sidebar.button("➕ New Chat"):
    chat_id = f"Chat {len(st.session_state.chats) + 1}"
    st.session_state.chats[chat_id] = []
    st.session_state.chat_files[chat_id] = None
    st.session_state.upload_counter[chat_id] = 0
    st.session_state.current_chat = chat_id

for chat_id in list(st.session_state.chats.keys()):
    col1, col2 = st.sidebar.columns([3, 1])

    if col1.button(chat_id, key=f"open_{chat_id}"):
        st.session_state.current_chat = chat_id

    if col2.button("❌", key=f"delete_{chat_id}"):
        del st.session_state.chats[chat_id]

        if chat_id in st.session_state.chat_files:
            del st.session_state.chat_files[chat_id]

        if chat_id in st.session_state.upload_counter:
            del st.session_state.upload_counter[chat_id]

        if st.session_state.current_chat == chat_id:
            st.session_state.current_chat = None

        st.rerun()

# ---------------------------
# Chat Area
# ---------------------------
if st.session_state.current_chat:

    chat_id = st.session_state.current_chat
    st.subheader(f"Current: {chat_id}")

    chat_history = st.session_state.chats[chat_id]

    # ---------------------------
    # Messages
    # ---------------------------
    for msg in chat_history:
        if msg.role == "user":
            st.markdown(f"<div class='user-msg'>{msg.content}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-msg'>{msg.content}</div>", unsafe_allow_html=True)

    # ---------------------------
    # INPUT BOX WRAPPER
    # ---------------------------
    st.markdown('<div class="input-box">', unsafe_allow_html=True)

    upload_key = f"upload_{chat_id}_{st.session_state.upload_counter[chat_id]}"

    with st.form("chat_form", clear_on_submit=True):

        col1, col2, col3 = st.columns([7, 1, 2])

        # Input
        with col1:
            user_input = st.text_input(
                "",
                placeholder="Type your message...",
                label_visibility="collapsed"
            )

        # Send
        with col2:
            submitted = st.form_submit_button("➤")

        # Upload (now properly inside box)
        with col3:
            uploaded_file = st.file_uploader(
                "",
                type="pdf",
                key=upload_key,
                label_visibility="collapsed"
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------
    # Upload Logic
    # ---------------------------
    def get_hash(file):
        return hashlib.md5(file.getvalue()).hexdigest()

    if uploaded_file:
        file_hash = get_hash(uploaded_file)

        if st.session_state.chat_files.get(chat_id) != file_hash:

            with st.spinner("Reading PDF..."):
                text = extract_pdf_text(uploaded_file)

                if not text:
                    response = "⚠️ No readable text found in this PDF."
                else:
                    messages = [
                        ChatMessage(role="user", content=f"Explain this document:\n{text[:3000]}")
                    ]
                    response = chat_once(messages)

            chat_history.append(ChatMessage(role="user", content=f"📄 {uploaded_file.name}"))
            chat_history.append(ChatMessage(role="assistant", content=response))

            st.session_state.chat_files[chat_id] = file_hash
            st.session_state.upload_counter[chat_id] += 1

            st.rerun()

    # ---------------------------
    # Send Logic
    # ---------------------------
    if submitted:
        if user_input.strip():

            chat_history.append(ChatMessage(role="user", content=user_input))

            bot_reply = chat_once(chat_history)

            chat_history.append(ChatMessage(role="assistant", content=bot_reply))

            st.rerun()
        else:
            st.warning("Enter something")