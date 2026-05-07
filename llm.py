import os
import chromadb

from mistralai.client import (
    MistralClient
)

from mistralai.models.chat_completion import (
    ChatMessage
)

from sentence_transformers import (
    SentenceTransformer
)

# ==========================================
# CONFIG
# ==========================================

MISTRAL_API_KEY = os.getenv(
    "MISTRAL_API_KEY"
)

if not MISTRAL_API_KEY:

    raise ValueError(
        "MISTRAL_API_KEY not found"
    )

CHROMA_DB_DIR = "diabetes_vector_db"

COLLECTION_NAME = "diabetes_rag"

# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("\n[+] Loading BGE-M3...")

embedding_model = SentenceTransformer(
    "BAAI/bge-m3",
    trust_remote_code=True
)

print("[+] Embedding Model Loaded")

# ==========================================
# LOAD VECTOR DB
# ==========================================

client_db = chromadb.PersistentClient(
    path=CHROMA_DB_DIR
)

collection = client_db.get_collection(
    name=COLLECTION_NAME
)

print("[+] Vector DB Loaded")

# ==========================================
# LOAD MISTRAL
# ==========================================

mistral_client = MistralClient(
    api_key=MISTRAL_API_KEY
)

print("[+] Mistral Connected")

# ==========================================
# RAG SEARCH
# ==========================================

def retrieve_context(query):

    # --------------------------------------
    # EMBED QUERY
    # --------------------------------------

    query_embedding = embedding_model.encode(
        query
    ).tolist()

    # --------------------------------------
    # VECTOR SEARCH
    # --------------------------------------

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
TITLE: {meta['title']}
URL: {meta['url']}

CONTENT:
{doc}

"""

    return context

# ==========================================
# CHAT LOOP
# ==========================================

while True:

    print("\n=================================")

    query = input(
        "\nAsk Question: "
    )

    if query.lower() == "exit":
        break

    # --------------------------------------
    # RETRIEVE CONTEXT
    # --------------------------------------

    context = retrieve_context(query)

    # --------------------------------------
    # SYSTEM PROMPT
    # --------------------------------------

    system_prompt = f"""
You are a medical AI assistant.

Answer ONLY using the provided context.

If answer is not present in context,
say:
"I could not find that information
in the medical database."

CONTEXT:
{context}
"""

    # --------------------------------------
    # SEND TO MISTRAL
    # --------------------------------------

    response = mistral_client.chat(

        model="mistral-small",

        messages=[

            ChatMessage(
                role="system",
                content=system_prompt
            ),

            ChatMessage(
                role="user",
                content=query
            )
        ],

        temperature=0.3,
        top_p=0.9
    )

    # --------------------------------------
    # PRINT ANSWER
    # --------------------------------------

    answer = (
        response
        .choices[0]
        .message
        .content
    )

    print("\n========== ANSWER ==========\n")

    print(answer)