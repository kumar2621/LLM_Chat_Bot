import chromadb

from sentence_transformers import (
    SentenceTransformer
)

# ==========================================
# CONFIG
# ==========================================

CHROMA_DB_DIR = "diabetes_vector_db"

COLLECTION_NAME = "diabetes_rag"

# ==========================================
# LOAD MODEL
# ==========================================

print("\n[+] Loading BGE-M3...")

model = SentenceTransformer(
    "BAAI/bge-m3",
    trust_remote_code=True
)

print("[+] Model Loaded")

# ==========================================
# LOAD VECTOR DB
# ==========================================

client = chromadb.PersistentClient(
    path=CHROMA_DB_DIR
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print("[+] Vector DB Loaded")

# ==========================================
# SEARCH LOOP
# ==========================================

while True:

    print("\n============================")

    query = input(
        "Ask Question: "
    )

    if query.lower() == "exit":
        break

    # --------------------------------------
    # EMBED QUERY
    # --------------------------------------

    query_embedding = model.encode(
        query
    ).tolist()

    # --------------------------------------
    # SEARCH VECTOR DB
    # --------------------------------------

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=3
    )

    # --------------------------------------
    # SHOW RESULTS
    # --------------------------------------

    print("\n========== RESULTS ==========\n")

    docs = results["documents"][0]

    metas = results["metadatas"][0]

    for i, (doc, meta) in enumerate(
        zip(docs, metas)
    ):

        print(f"\nRESULT {i+1}")
        print("-" * 50)

        print(
            f"TITLE: "
            f"{meta['title']}"
        )

        print(
            f"URL: "
            f"{meta['url']}"
        )

        print("\nCONTENT:\n")

        print(doc[:1000])

        print("\n" + "=" * 60)