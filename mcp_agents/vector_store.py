# mcp_agents/vector_store.py

import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

DATA_DIR = "data"

def get_book_path(title):
    filename = title.lower().replace(" ", "_") + ".txt"
    return os.path.join(DATA_DIR, filename)

def is_book_downloaded(title):
    return os.path.exists(get_book_path(title))

# Initialize SentenceTransformer model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize persistent ChromaDB client
chroma_client = chromadb.Client(Settings(
    persist_directory="db",
    anonymized_telemetry=False
))

collection = chroma_client.get_or_create_collection("books")

def is_book_ingested(title):
    results = collection.get(where={"title": title})
    return bool(results and results["ids"])

def clean_gutenberg_text(text):
    lines = text.splitlines()
    clean_lines = []
    in_main_content = False
    start_found = False
    end_found = False

    for line in lines:
        if '*** start of' in line.lower():
            in_main_content = True
            start_found = True
            continue
        if '*** end of' in line.lower():
            end_found = True
            break
        if in_main_content:
            clean_lines.append(line.strip())

    if start_found and end_found:
        return "\n".join(clean_lines).strip()
    else:
        # fallback to return the entire text if markers not found
        return text.strip()

def ingest_book(title, raw_text):
    clean_text = clean_gutenberg_text(raw_text)
    if not clean_text.strip():
        print("[!] No text chunks found to ingest.")
        return

    chunks = [clean_text[i:i + 1000] for i in range(0, len(clean_text), 1000)]
    embeddings = model.encode(chunks).tolist()
    ids = [f"{title}_chunk_{i}" for i in range(len(chunks))]

    # --- MODIFICATION START ---
    metadatas = []
    for i in range(len(chunks)):
        metadatas.append({"title": title, "chunk_id": i}) # Add chunk_id here
    # --- MODIFICATION END ---

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas # Use the new metadatas list
    )

    print(f"[✔] Book '{title}' ingested with {len(chunks)} chunks.")

def query_book(title, query, top_k=5):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k, where={"title": title})
    return results["documents"][0] if results["documents"] else []

def get_last_chunk(title: str):
    # Retrieve all results for the given title
    # We need to include 'metadatas' and 'documents' for this to work
    results = collection.get(where={"title": title}, include=['metadatas', 'documents'])

    if not results or not results.get("documents"):
        return ""

    # Find chunk with max chunk_id
    max_chunk = None
    max_id = -1
    
    # Ensure metadatas and documents are lists of the same length
    if len(results["metadatas"]) != len(results["documents"]):
        print(f"Warning: Mismatch between metadatas and documents for title '{title}'.")
        return ""

    for i in range(len(results["documents"])):
        doc = results["documents"][i]
        meta = results["metadatas"][i]
        
        chunk_id = meta.get("chunk_id")
        if chunk_id is not None: # Check if chunk_id exists and is not None
            chunk_id = int(chunk_id) # Ensure it's an integer
            if chunk_id > max_id:
                max_id = chunk_id
                max_chunk = doc

    return max_chunk if max_chunk else "" # Return empty string if no max_chunk found