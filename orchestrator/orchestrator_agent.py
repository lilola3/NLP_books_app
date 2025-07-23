# orchestrator/orchestrator_agent.py

import os
from mcp_agents.gutenberg_api import GutenbergAPI # Import the class
from mcp_agents.vector_store import is_book_ingested, ingest_book, query_book, get_last_chunk, get_book_path, is_book_downloaded # Added get_book_path
from mcp_agents.llm_gateway import call_llm
from mcp_agents.prompt import build_question_prompt, build_summary_prompt, build_continuation_prompt, parse_intent_and_title

# Removed redundant import:
# from mcp_agents.gutenberg_api import download_book, get_book_details # REMOVE THIS LINE
# from mcp_agents.vector_store import is_book_downloaded # REMOVE THIS LINE (already imported above)


DATA_FOLDER = "data"

def ensure_book_available_and_ingested(book_info: dict) -> str:
    # book_info should contain at least 'gutenberg_id' and 'title'
    gutenberg_id = book_info.get('gutenberg_id')
    title = book_info.get('title')

    if not title or not gutenberg_id:
        print(f"[!] Invalid book_info received: {book_info}")
        return None

    # Step 1: Check if the book is downloaded
    # is_book_downloaded and get_book_path are from vector_store
    if not is_book_downloaded(title):
        print(f"🔄 Downloading '{title}'...")
        # Call download_book as a static method of GutenbergAPI
        raw_text = GutenbergAPI.download_book(gutenberg_id) 
        if not raw_text:
            print(f"[!] Failed to download '{title}'.")
            return None
        # Save the downloaded book
        with open(get_book_path(title), "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"✅ '{title}' downloaded.")
    else:
        print(f"✅ '{title}' already downloaded.")
        # Ensure raw_text is available for ingestion if needed
        with open(get_book_path(title), "r", encoding="utf-8") as f:
            raw_text = f.read() 

    # Step 2: Check if the book is ingested (embeddings in ChromaDB)
    if not is_book_ingested(title):
        print(f"🧠 Ingesting '{title}' into vector store...")
        # Ensure raw_text is available if it was only downloaded previously
        if not raw_text: 
            with open(get_book_path(title), "r", encoding="utf-8") as f:
                raw_text = f.read()
        
        ingest_book(title, raw_text)
        
    else:
        print(f"🧠 '{title}' already ingested. Skipping ingestion.")
    
    return title # Return the verified title

def orchestrate_request(user_input: str, current_remembered_title: str | None) -> tuple[str, str | None]:
    """
    Orchestrates the user's request, handling intent, title extraction, and execution.
    Returns a tuple: (response_string, new_remembered_title)
    """
    parsed_input = parse_intent_and_title(user_input, current_remembered_title)
    intent = parsed_input.get("intent")
    extracted_title = parsed_input.get("title")

    # Determine the book title to work with
    # If LLM extracted a new title and intent is 'switch_book', use it.
    # Otherwise, stick with the current_remembered_title.
    active_title = current_remembered_title
    if extracted_title and intent == "switch_book":
        # Attempt to switch to the new book
        print(f"Attempting to switch to '{extracted_title}'...")
        books_found = GutenbergAPI.search_books({"title": extracted_title})
        if books_found:
            selected_book_info = books_found[0] # Take the first result
            verified_title = ensure_book_available_and_ingested(selected_book_info)
            if verified_title:
                active_title = verified_title
                response = f"📖 Switched to '{active_title}'. How can I help you with this book?"
                return response, active_title
            else:
                response = f"❌ Could not make '{extracted_title}' available. Continuing with '{current_remembered_title or 'no book'}'. Try another title for switching."
                return response, current_remembered_title
        else:
            response = f"❌ Cannot find book '{extracted_title}'. Continuing with '{current_remembered_title or 'no book'}'. "
            return response, current_remembered_title
    elif not active_title and (intent == "summary" or intent == "continuation" or intent == "question"):
        return "Please specify which book you are asking about, or search for one first.", None


    # If we are here, active_title is set (either from remembered_title or after a successful switch)
    # And the intent is not 'switch_book' or 'switch_book' failed.

    if intent == "summary":
        # A more robust way to get all chunks for summary (suggested in previous turn):
        # In vector_store.py, add:
        # def get_all_chunks_for_title(title: str):
        #    results = collection.get(where={"title": title}, include=['documents'])
        #    return results['documents'] if results and results['documents'] else []
        #
        # Then here:
        # all_chunks = get_all_chunks_for_title(active_title)
        # prompt = build_summary_prompt(active_title, all_chunks)
        # For demonstration, let's use some context from vector store:
        context_chunks = query_book(active_title, f"Summarize '{active_title}'", top_k=5) # still uses query
        prompt = build_summary_prompt(active_title, context_chunks)
        response = call_llm(prompt)
    elif intent == "continuation":
        last_chunk = get_last_chunk(active_title)
        if not last_chunk:
            response = f"I cannot find the last part of '{active_title}' to continue the story."
        else:
            prompt = build_continuation_prompt(active_title, last_chunk)
            response = call_llm(prompt)
    elif intent == "question":
        # For questions, we need the user's original input as the question
        context_chunks = query_book(active_title, user_input, top_k=5)
        context = "\n\n".join(context_chunks)
        prompt = build_question_prompt(active_title, context, user_input)
        response = call_llm(prompt)
    else: # This covers unknown intents
        response = "Sorry, I didn't understand your request."

    return response, active_title