import json
import chromadb

from sentence_transformers import (
    SentenceTransformer
)

# ==========================================
# CONFIG
# ==========================================

INPUT_FILE = "final_filtered_dataset.jsonl"

CHROMA_DB_DIR = "diabetes_vector_db"

COLLECTION_NAME = "diabetes_rag"

# ==========================================
# LOAD MODEL
# ==========================================

print("\n[+] Loading BGE-M3 Model...")

model = SentenceTransformer(
    "BAAI/bge-m3",
    trust_remote_code=True
)

print("[+] Model Loaded")

# ==========================================
# CREATE CHROMA DB
# ==========================================

client = chromadb.PersistentClient(
    path=CHROMA_DB_DIR
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

# ==========================================
# CHUNK FUNCTION
# ==========================================

def chunk_text(
    text,
    chunk_size=350,
    overlap=70
):

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks

# ==========================================
# PROCESS DATASET
# ==========================================

doc_count = 0
chunk_count = 0

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    for line in f:

        try:

            data = json.loads(line)

            url = data.get(
                "url",
                ""
            )

            title = data.get(
                "title",
                ""
            )

            content = data.get(
                "content",
                ""
            )

            # ---------------------------------
            # CHUNK DOCUMENT
            # ---------------------------------

            chunks = chunk_text(content)

            # ---------------------------------
            # PROCESS CHUNKS
            # ---------------------------------

            for idx, chunk in enumerate(chunks):

                # skip tiny chunks
                if len(chunk.split()) < 80:
                    continue

                # -----------------------------
                # CREATE EMBEDDING
                # -----------------------------

                embedding = model.encode(
                    chunk
                ).tolist()

                # -----------------------------
                # UNIQUE CHUNK ID
                # -----------------------------

                chunk_id = (
                    f"{doc_count}_{idx}"
                )

                # -----------------------------
                # STORE IN VECTOR DB
                # -----------------------------

                collection.add(

                    ids=[chunk_id],

                    embeddings=[embedding],

                    documents=[chunk],

                    metadatas=[{
                        "url": url,
                        "title": title,
                        "chunk": idx
                    }]
                )

                chunk_count += 1

                print(
                    f"[+] Stored Chunk "
                    f"{chunk_count}"
                )

            doc_count += 1

        except Exception as e:

            print("ERROR:", e)

# ==========================================
# DONE
# ==========================================

print("\n================================")
print("VECTOR DATABASE CREATED")
print("================================")
print(f"Documents: {doc_count}")
print(f"Chunks: {chunk_count}")
print(f"DB Path: {CHROMA_DB_DIR}")
print("================================")