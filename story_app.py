import sys
import streamlit as st
import requests
import json
import os

print(f"DEBUG: Python executable: {sys.executable}")
print(f"DEBUG: sys.path: {sys.path}")

# ... rest of your app.py code ...
# Import your backend logic
from orchestrator.orchestrator_agent import orchestrate_request, ensure_book_available_and_ingested
from mcp_agents.gutenberg_api import GutenbergAPI

CHAT_HISTORY_FILE = "chat_history.json"
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True) # Ensure data directory exists

# --- Safely load chat threads as a dict ---
if os.path.exists(CHAT_HISTORY_FILE):
    try:
        with open(CHAT_HISTORY_FILE, "r") as f:
            all_threads = json.load(f)
        if not isinstance(all_threads, dict):
            all_threads = {}
    except json.JSONDecodeError:
        all_threads = {}
else:
    all_threads = {}

# Store all_threads in session state once
if "all_threads" not in st.session_state:
    st.session_state.all_threads = all_threads

# Initialize messages if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize current_thread if not exists
if "current_thread" not in st.session_state:
    st.session_state.current_thread = None

# Initialize remembered_title for the book assistant backend
if "remembered_title" not in st.session_state:
    st.session_state.remembered_title = None

st.set_page_config(page_title="📖 Resume a Story, or Start a New Chapter", layout="centered")

st.sidebar.title("📂 Chat Threads")

thread_names = list(st.session_state.all_threads.keys())
selected_thread = st.sidebar.selectbox("Select a thread", ["➕ New Thread"] + thread_names, key="thread_selector")

# Handle new thread creation
if selected_thread == "➕ New Thread":
    new_name = st.sidebar.text_input("Enter new thread name:")
    if new_name and st.sidebar.button("Create Thread"):
        if new_name not in st.session_state.all_threads:
            st.session_state.all_threads[new_name] = []
            st.session_state.current_thread = new_name
            st.session_state.messages = []
            # Reset remembered_title when starting a new thread
            st.session_state.remembered_title = None 
            with open(CHAT_HISTORY_FILE, "w") as f:
                json.dump(st.session_state.all_threads, f)
            st.rerun()
        else:
            st.sidebar.error("Thread name already exists!")

# Handle thread switching
if selected_thread != "➕ New Thread" and st.session_state.current_thread != selected_thread:
    st.session_state.current_thread = selected_thread
    st.session_state.messages = st.session_state.all_threads.get(selected_thread, [])
    # When switching threads, you might want to reset the remembered_title
    # or load it from the thread history if you store it there.
    # For now, let's keep it simple: assume each thread can imply a different book,
    # so we might reset it or allow the first query to set it.
    # If each thread should remember its book, you'd need to save `remembered_title`
    # within `all_threads[thread_name]` data structure.
    # For simplicity, let's reset it for now.
    st.session_state.remembered_title = None # Reset remembered_title on thread switch
    st.rerun() # Rerun to load messages and potentially the remembered_title

def save_chat_history():
    if st.session_state.current_thread and st.session_state.current_thread != "➕ New Thread":
        st.session_state.all_threads[st.session_state.current_thread] = st.session_state.messages
        with open(CHAT_HISTORY_FILE, "w") as f:
            json.dump(st.session_state.all_threads, f)

# Display title
current_display_name = st.session_state.current_thread if st.session_state.current_thread else "New Story"
st.title(f"📖 {current_display_name}")

# --- Book Selection UI (if no book is remembered) ---
if not st.session_state.remembered_title:
    st.info("No book selected. Please search for a book to begin your story.")
    book_search_query = st.text_input("Search for a book (title or author):", key="book_search_input")
    
    # Store search results in session state to persist across reruns
    if "last_search_results" not in st.session_state:
        st.session_state.last_search_results = []

    if book_search_query:
        # Perform search and store in session state
        # Limiting to top 5 as per your requirement
        st.session_state.last_search_results = GutenbergAPI.search_books({"title": book_search_query})[:5] 

        if st.session_state.last_search_results:
            st.subheader("Search Results (Top 5):")
            
            # Create a list of display strings for the radio buttons
            book_options_display = []
            for i, book in enumerate(st.session_state.last_search_results):
                # Include Author, Title, and potentially other useful info like Gutenberg ID or publication year
                # Make sure these keys exist in your GutenbergAPI search result dictionary
                title = book.get('title', 'N/A')
                author = book.get('author', 'N/A')
                gutenberg_id = book.get('gutenberg_id', 'N/A')
                book_options_display.append(f"{i+1}. **{title}** by {author} (ID: {gutenberg_id})")
            
            # Use a radio button for selection. The index of the selected option is returned.
            selected_book_idx = st.radio(
                "Select a book from the results:", 
                options=range(len(st.session_state.last_search_results)), 
                format_func=lambda i: book_options_display[i], 
                key="book_radio_select"
            )
            
            # Display the selected book's full details (optional, but good for verification)
            if selected_book_idx is not None:
                selected_book_info_for_display = st.session_state.last_search_results[selected_book_idx]
                st.write(f"You selected: **{selected_book_info_for_display.get('title', 'N/A')}** by {selected_book_info_for_display.get('author', 'N/A')}")
            
            if st.button("Select This Book", key="select_book_button"):
                # Get the actual book dictionary from the stored search results
                selected_book_info = st.session_state.last_search_results[selected_book_idx]
                
                with st.spinner(f"Making '{selected_book_info['title']}' available..."):
                    verified_title = ensure_book_available_and_ingested(selected_book_info)
                    if verified_title:
                        st.session_state.remembered_title = verified_title
                        st.success(f"Successfully loaded '{verified_title}'!")
                        st.session_state.last_search_results = [] # Clear results after selection
                        st.rerun() # Rerun to update the main app UI and hide book selection
                    else:
                        st.error(f"Failed to load '{selected_book_info['title']}'. Please try another.")
        else:
            st.warning("No books found for your search. Try a different query.")
    # This else-if handles if a query was made but no results, or if the user hasn't typed anything yet
    elif not book_search_query and st.session_state.last_search_results:
        # If there were previous results but the search bar is empty, clear them
        st.session_state.last_search_results = []
        st.rerun() # Rerun to clear the displayed results
elif st.session_state.remembered_title:
    st.info(f"Currently discussing: **{st.session_state.remembered_title}**")


# Display chat history
chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

st.markdown("<div style='height: 200px;'></div>", unsafe_allow_html=True) # Spacer

# Input section
input_container = st.container()
with input_container:
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.chat_input("The story paused, the adventure waits… which book shall we resume today?", key="chat_input")
    with col2:
        # File uploader might be tricky to map directly to a book assistant
        # You'd probably want to use the file content as a direct query or
        # allow uploading new books for ingestion here.
        # For simplicity, let's keep it as a prompt input for now.
        uploaded_file = st.file_uploader("📎", type=["txt"], label_visibility="collapsed", key="file_uploader")

# Handle user input
if user_input:
    # Check if we have a valid thread
    if not st.session_state.current_thread or st.session_state.current_thread == "➕ New Thread":
        st.error("Please select or create a thread first!")
    elif not st.session_state.remembered_title: # Check if a book is selected
        st.error("Please select a book first using the search bar above!")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_chat_history()

        with chat_placeholder:
            with st.chat_message("user"):
                st.write(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."): # Add a spinner while processing
                    try:
                        # Call your orchestrator backend
                        response_text, new_remembered_title = orchestrate_request(user_input, st.session_state.remembered_title)
                        
                        # Update remembered_title in session state
                        st.session_state.remembered_title = new_remembered_title

                        st.write(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        save_chat_history()
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        import traceback
                        st.error(traceback.format_exc()) # Show full traceback in UI for debugging
        st.rerun() # Rerun to clear chat input and update display


# Handle file upload (similar modification as user_input)
elif uploaded_file:
    # Check if we have a valid thread
    if not st.session_state.current_thread or st.session_state.current_thread == "➕ New Thread":
        st.error("Please select or create a thread first!")
    elif not st.session_state.remembered_title: # Check if a book is selected
        st.error("Please select a book first using the search bar above!")
    else:
        file_content = uploaded_file.read().decode("utf-8")
        truncated_content = file_content[:500] # For display in chat
        st.session_state.messages.append({"role": "user", "content": f"Uploaded file (first 500 chars): {truncated_content}"})
        save_chat_history()

        with chat_placeholder:
            with st.chat_message("user"):
                st.write(f"(from file) {truncated_content}{'...' if len(file_content) > 500 else ''}")
            with st.chat_message("assistant"):
                with st.spinner("Processing file..."): # Add a spinner
                    try:
                        # For file uploads, you need to decide how your backend handles it.
                        # If the backend is designed to *ingest* a new book from a file,
                        # you'd need a specific orchestrator function for that, or modify orchestrate_request
                        # to detect file upload intent.
                        # For now, let's treat the file content as a long user input/query.
                        # This might hit LLM context limits if the file is very large.
                        response_text, new_remembered_title = orchestrate_request(file_content, st.session_state.remembered_title)

                        st.session_state.remembered_title = new_remembered_title

                        st.write(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        save_chat_history()
                    except Exception as e:
                        st.error(f"An error occurred processing file: {e}")
                        import traceback
                        st.error(traceback.format_exc()) # Show full traceback in UI for debugging
        st.rerun() # Rerun to clear file uploader state and update display


# Add delete thread functionality
if st.session_state.current_thread and st.session_state.current_thread != "➕ New Thread":
    if st.sidebar.button("🗑️ Delete Current Thread"):
        if st.session_state.current_thread in st.session_state.all_threads:
            del st.session_state.all_threads[st.session_state.current_thread]
            with open(CHAT_HISTORY_FILE, "w") as f:
                json.dump(st.session_state.all_threads, f)
            st.session_state.current_thread = None
            st.session_state.messages = []
            st.session_state.remembered_title = None # Reset book on thread delete
            st.rerun()