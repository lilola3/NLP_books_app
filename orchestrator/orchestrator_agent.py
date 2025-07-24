# orchestrator/orchestrator_agent.py

import os
from mcp_agents.gutenberg_api import GutenbergAPI
from mcp_agents.llm_gateway import call_llm
# Make sure your prompt.py has the build_summary_prompt that accepts a string, as modified above
from mcp_agents.prompt import build_question_prompt, build_summary_prompt, build_continuation_prompt, parse_intent_and_title
from mcp_agents.vector_store import is_book_ingested, ingest_book, query_book, get_last_chunk, get_book_path, is_book_downloaded


DATA_FOLDER = "data"

def ensure_book_available_and_ingested(book_info: dict) -> str | None:
    gutenberg_id = book_info.get('gutenberg_id')
    title = book_info.get('title')

    if not title or not gutenberg_id:
        print(f"[!] Invalid book_info received: {book_info}")
        return None

    # Step 1: Check if the book is downloaded
    if not is_book_downloaded(title):
        print(f"🔄 Downloading '{title}'...")
        raw_text = GutenbergAPI.download_book(gutenberg_id) 
        if not raw_text:
            print(f"[!] Failed to download '{title}'.")
            return None
        with open(get_book_path(title), "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"✅ '{title}' downloaded.")
    else:
        print(f"✅ '{title}' already downloaded.")
        # Ensure raw_text is loaded if already downloaded but not in memory
        with open(get_book_path(title), "r", encoding="utf-8") as f:
            raw_text = f.read() 

    # Step 2: Check if the book is ingested (embeddings in ChromaDB)
    if not is_book_ingested(title):
        print(f"🧠 Ingesting '{title}' into vector store...")
        if not raw_text: # Ensure raw_text is available if it was only downloaded previously
            with open(get_book_path(title), "r", encoding="utf-8") as f:
                raw_text = f.read()
        
        ingestion_success = ingest_book(title, raw_text)
        if not ingestion_success:
            print(f"[!] Ingestion failed for '{title}'.")
            return None
        else:
            print(f"🧠 '{title}' ingested.")
    else:
        print(f"🧠 '{title}' already ingested. Skipping ingestion.")
    
    return title

def orchestrate_request(user_input: str, current_remembered_title: str | None) -> tuple[str, str | None]:
    """
    Orchestrates the user's request, handling intent, title extraction, and execution.
    Returns a tuple: (response_string, new_remembered_title)
    """
    parsed_input = parse_intent_and_title(user_input, current_remembered_title)
    intent = parsed_input.get("intent")
    extracted_title = parsed_input.get("title")

    # Determine the book title to work with
    active_title = current_remembered_title
    
    # If the LLM specifically detected a request to switch book
    if intent == "switch_book":
        if extracted_title:
            print(f"Attempting to switch to '{extracted_title}'...")
            books_found = GutenbergAPI.search_books({"title": extracted_title})
            if books_found:
                selected_book_info = books_found[0]
                verified_title = ensure_book_available_and_ingested(selected_book_info)
                if verified_title:
                    active_title = verified_title
                    response = f"📖 Switched to '{active_title}'. How can I help you with this book?"
                    return response, active_title
                else:
                    response = f"❌ Could not make '{extracted_title}' available. Continuing with '{current_remembered_title or 'no book'}'. Try another title for switching."
                    return response, current_remembered_title
            else:
                response = f"❌ Cannot find book '{extracted_title}' to switch to. Continuing with '{current_remembered_title or 'no book'}'. "
                return response, current_remembered_title
        else:
            return "Please provide a book title or ID to switch to.", current_remembered_title
            
    if active_title is None:
        return "Please specify which book you are asking about, or search for one first (e.g., 'Search for Moby Dick').", None

    if intent == "summary":
        search_query_for_vector_store = f"summary of the book {active_title}"
        # Increased top_k for summary, since we're truncating anyway.
        # This gives a broader initial context before trimming.
        context_chunks = query_book(active_title, search_query_for_vector_store, top_k=10) 
        
        context = "\n\n".join(context_chunks)
        
        # --- SIMPLE TRUNCATION FOR SUMMARIZATION (PRIORITIZING SIMPLICITY OVER ACCURACY) ---
        if len(context) > 3000:
            print(f"WARNING: Summary context too long ({len(context)} chars), truncating to 3000 chars.")
            context = context[:3000]
        # ---------------------------------------------------------------------------------

        if not context.strip():
            response = f"I don't have enough information to summarize '{active_title}'. It might not be fully ingested or I couldn't retrieve relevant content."
        else:
            prompt = build_summary_prompt(active_title, context) # Pass context as string
            response = call_llm(prompt)

    elif intent == "continuation":
        last_chunk = get_last_chunk(active_title)
        if not last_chunk:
            response = f"I cannot find the last part of '{active_title}' to continue the story."
        else:
            prompt = build_continuation_prompt(active_title, last_chunk)
            response = call_llm(prompt)

    elif intent == "question":
        search_query_for_vector_store = f"{user_input} from {active_title}" 
        
        context_chunks = query_book(active_title, search_query_for_vector_store, top_k=5)
        context = "\n\n".join(context_chunks)
        
        # --- SIMPLE TRUNCATION FOR QUESTION CONTEXT (PRIORITIZING SIMPLICITY OVER ACCURACY) ---
        if len(context) > 3000: # Apply truncation here too for consistency and safety
            print(f"WARNING: Question context too long ({len(context)} chars), truncating to 3000 chars.")
            context = context[:3000]
        # -------------------------------------------------------------------------------------

        if not context.strip():
            response = f"I couldn't find specific information related to '{user_input}' in '{active_title}'. The book might not be fully ingested or the query is too specific for the available content."
        else:
            prompt = build_question_prompt(active_title, context, user_input)
            response = call_llm(prompt)
            
    else:
        response = "Sorry, I didn't understand your request."

    return response, active_title