import streamlit as st
import chromadb

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from sentence_transformers import (
    SentenceTransformer
)

import os

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Diabetes Assistant",
    layout="centered"
)

st.title("Scooby Chatbot")

# ==========================================
# LOAD API KEY
# ==========================================

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise ValueError("MISTRAL_API_KEY not found")

# ==========================================
# LOAD MISTRAL
# ==========================================

mistral_client = MistralClient(
    api_key=api_key
)

# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

@st.cache_resource
def load_embedding_model():

    return SentenceTransformer(
        "BAAI/bge-m3",
        trust_remote_code=True
    )

embedding_model = load_embedding_model()

# ==========================================
# LOAD VECTOR DB
# ==========================================

@st.cache_resource
def load_vector_db():

    client = chromadb.PersistentClient(
        path="diabetes_vector_db"
    )

    collection = client.get_collection(
        name="diabetes_rag"
    )

    return collection

collection = load_vector_db()

# ==========================================
# UI CSS
# ==========================================

st.markdown("""
<style>

/* Chat bubbles */
.user-msg {
    text-align: right;
    background: #2b2b2b;
    padding: 12px;
    border-radius: 12px;
    margin: 5px 0;
    color: white;
}

.bot-msg {
    text-align: left;
    background: #1e1e1e;
    padding: 12px;
    border-radius: 12px;
    margin: 5px 0;
    color: white;
}

/* Input container */
.input-box {
    border: 1px solid #2f2f2f;
    border-radius: 16px;
    padding: 12px;
    background-color: #111;
    margin-top: 20px;
}

/* Align everything */
div[data-testid="stHorizontalBlock"] {
    align-items: center;
}

/* Text input */
input {
    height: 44px !important;
    border-radius: 10px !important;
}

/* Send button */
button[kind="secondary"] {
    height: 44px !important;
    min-width: 50px !important;
    border-radius: 10px !important;
}

/* Hide labels */
div[data-testid="stTextInput"] label {
    display: none;
}

/* Sidebar buttons */
.stSidebar button {
    width: 100%;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STORAGE
# ==========================================

if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

# ==========================================
# CREATE DEFAULT CHAT
# ==========================================

if not st.session_state.current_chat:

    chat_id = (
        f"Chat "
        f"{len(st.session_state.chats)+1}"
    )

    st.session_state.chats[chat_id] = []

    st.session_state.current_chat = chat_id

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("Chats")

if st.sidebar.button("➕ New Chat"):

    chat_id = (
        f"Chat "
        f"{len(st.session_state.chats)+1}"
    )

    st.session_state.chats[chat_id] = []

    st.session_state.current_chat = chat_id

for chat_id in list(
    st.session_state.chats.keys()
):

    col1, col2 = st.sidebar.columns([3, 1])

    # open chat
    if col1.button(
        chat_id,
        key=f"open_{chat_id}"
    ):

        st.session_state.current_chat = chat_id

    # delete chat
    if col2.button(
        "❌",
        key=f"delete_{chat_id}"
    ):

        del st.session_state.chats[
            chat_id
        ]

        if (
            st.session_state.current_chat
            == chat_id
        ):

            st.session_state.current_chat = None

        st.rerun()

# ==========================================
# RAG RETRIEVAL
# ==========================================

def retrieve_context(query):

    query_embedding = (
        embedding_model.encode(query)
        .tolist()
    )

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=3
    )

    docs = results["documents"][0]

    metas = results["metadatas"][0]

    context = ""

    for i, (doc, meta) in enumerate(
        zip(docs, metas)
    ):

        context += f"""

SOURCE {i+1}

TITLE:
{meta['title']}

URL:
{meta['url']}

CONTENT:
{doc}

"""

    return context

# ==========================================
# CHAT FUNCTION
# ==========================================

def rag_chat(user_query):

    context = retrieve_context(
        user_query
    )

    system_prompt = f"""
You are a helpful medical AI assistant.

Answer ONLY from the provided context.

If answer is not found,
say:
"I could not find that information in the medical database."

CONTEXT:
{context}
"""

    response = mistral_client.chat(

        model="mistral-small",

        messages=[

            ChatMessage(
                role="system",
                content=system_prompt
            ),

            ChatMessage(
                role="user",
                content=user_query
            )
        ],

        temperature=0.3,
        top_p=0.9
    )

    return (
        response
        .choices[0]
        .message
        .content
    )

# ==========================================
# CHAT AREA
# ==========================================

if st.session_state.current_chat:

    chat_id = (
        st.session_state.current_chat
    )

    st.subheader(f"Current: {chat_id}")

    chat_history = (
        st.session_state.chats[chat_id]
    )

    # ======================================
    # DISPLAY MESSAGES
    # ======================================

    for msg in chat_history:

        if msg.role == "user":

            st.markdown(
                f"<div class='user-msg'>"
                f"{msg.content}"
                f"</div>",
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"<div class='bot-msg'>"
                f"{msg.content}"
                f"</div>",
                unsafe_allow_html=True
            )

    # ======================================
    # INPUT BOX
    # ======================================

    st.markdown(
        '<div class="input-box">',
        unsafe_allow_html=True
    )

    with st.form(
        "chat_form",
        clear_on_submit=True
    ):

        col1, col2 = st.columns([8, 1])

        # input
        with col1:

            user_input = st.text_input(
                "Message Input",
                placeholder="Ask medical question...",
                label_visibility="collapsed"
            )

        # send button
        with col2:

            submitted = (
                st.form_submit_button("➤")
            )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )

    # ======================================
    # SEND LOGIC
    # ======================================

    if submitted:

        if user_input.strip():

            # add user msg
            chat_history.append(

                ChatMessage(
                    role="user",
                    content=user_input
                )
            )

            with st.spinner(
                "Thinking..."
            ):

                bot_reply = rag_chat(
                    user_input
                )

            # add assistant msg
            chat_history.append(

                ChatMessage(
                    role="assistant",
                    content=bot_reply
                )
            )

            st.rerun()

        else:

            st.warning(
                "Enter something"
            )