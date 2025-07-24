# mcp_agents/vector_store.py

import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
# from langchain.text_splitter import RecursiveCharacterTextSplitter # You might need this if you implement more advanced chunking


DATA_DIR = "data"

def get_book_path(title):
    filename = title.lower().replace(" ", "_").replace(":", "").replace("'", "").replace(",", "") + ".txt"
    return os.path.join(DATA_DIR, filename)

def is_book_downloaded(title):
    return os.path.exists(get_book_path(title))

# Initialize SentenceTransformer model once
model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize persistent ChromaDB client
chroma_client = chromadb.Client(Settings(
    persist_directory=os.path.join(DATA_DIR, "db"), # Store DB inside data folder
    anonymized_telemetry=False
))

collection = chroma_client.get_or_create_collection("books")

def is_book_ingested(title):
    # Check by counting documents for the title
    # Note: collection.count() is for the whole collection.
    # collection.get(where={"title": title}, limit=1) is better for checking existence.
    results = collection.get(where={"title": title}, limit=1)
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
        return False # Return False to indicate failure

    # Simple fixed-size chunking as you have it
    # Consider using langchain's RecursiveCharacterTextSplitter for better chunking
    chunks = [clean_text[i:i + 1000] for i in range(0, len(clean_text), 1000)]
    embeddings = model.encode(chunks).tolist()
    ids = [f"{title.replace(' ', '_').replace(':', '')}_chunk_{i}" for i in range(len(chunks))] # Ensure IDs are valid and unique

    metadatas = []
    for i in range(len(chunks)):
        metadatas.append({"title": title, "chunk_id": i}) 

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas 
    )

    print(f"[✔] Book '{title}' ingested with {len(chunks)} chunks.")
    return True # Indicate success

def query_book(title: str, query: str, top_k: int = 5) -> list[str]:
    """
    Queries the vector store for relevant chunks from a specific book.
    Returns a list of strings (chunks). Returns an empty list if no results.
    """
    try:
        query_embedding = model.encode([query]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where={"title": title}, # Filter by book title
            include=['documents']
        )
        
        if results and results.get("documents"):
            # results["documents"] is a list of lists, e.g., [['doc1'], ['doc2']]
            # Flatten this into a single list of strings
            flat_documents = [doc for sublist in results["documents"] for doc in sublist]
            return flat_documents
        else:
            return [] # IMPORTANT: Return an empty list if no results
    except Exception as e:
        print(f"Error querying book '{title}': {e}")
        return [] # IMPORTANT: Return an empty list on error



def get_last_chunk(title: str) -> str:
    """
    Retrieves the last ingested chunk for a specific book based on chunk_id.
    Returns a string. Returns an empty string if no chunks.
    """
    try:
        # Fetch all chunks for the given title
        all_chunks_data = collection.get(
            where={"title": title},
            include=['metadatas', 'documents']
        )

        if not all_chunks_data or not all_chunks_data.get("documents"):
            return ""

        max_chunk_id = -1
        last_chunk_content = ""
        
        for i in range(len(all_chunks_data["documents"])):
            doc = all_chunks_data["documents"][i]
            meta = all_chunks_data["metadatas"][i]
            
            chunk_id = meta.get("chunk_id")
            if chunk_id is not None:
                # Ensure chunk_id is an integer, it might be stored as float if coming from JSON
                try:
                    chunk_id = int(chunk_id)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid chunk_id '{chunk_id}' for title '{title}'. Skipping.")
                    continue
                
                if chunk_id > max_chunk_id:
                    max_chunk_id = chunk_id
                    last_chunk_content = doc

        return last_chunk_content if last_chunk_content else "" # Return empty string if no max_chunk found
    except Exception as e:
        print(f"Error getting last chunk for '{title}': {e}")
        return "" # IMPORTANT: Return empty string on error