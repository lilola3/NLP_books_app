import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.Client(Settings(
    persist_directory="db",
    anonymized_telemetry=False
))

collection = chroma_client.get_or_create_collection("books")

def is_book_ingested(title):
    results = collection.get(where={"title": title})
    return bool(results and results["ids"])

def ingest_book(title, text, chunk_size=500, overlap=100):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)

    embeddings = model.encode(chunks).tolist()
    ids = [f"{title}_{i}" for i in range(len(chunks))]

    collection.add(documents=chunks, embeddings=embeddings, ids=ids,
                   metadatas=[{"title": title}] * len(chunks))

def query_book(title, query, top_k=5):
    query_embedding = model.encode(query).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k, where={"title": title})
    return results["documents"][0] if results["documents"] else []

def get_last_chunk(title):
    results = collection.get(where={"title": title})
    if results and "documents" in results and results["documents"]:
        return results["documents"][-1]  # last embedded chunk
    return "The story continues..."

