# main.py

import os
from mcp_agents.gutenberg_api import GutenbergAPI
from orchestrator.orchestrator_agent import ensure_book_available_and_ingested, orchestrate_request # Import new orchestrator function

DATA_FOLDER = "data"
remembered_title = None  # Keep current book title across queries

def search_and_select_book():
    """Handles the book search and selection process."""
    while True:
        query = input("Enter book title or author to search: ").strip()
        if not query:
            print("Please enter something.")
            continue

        results = GutenbergAPI.search_books({"title": query})
        if not results:
            print("No results found. Try again.")
            continue

        print("\nSearch results:")
        for i, book in enumerate(results, start=1):
            print(f"{i}. {book['title']} — {book['author']}")

        choice = input("Select a book by number or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            return None

        if not choice.isdigit() or not (1 <= int(choice) <= len(results)):
            print("Invalid choice. Please enter a valid number.")
            continue

        selected = results[int(choice) - 1]
        print(f"You selected: {selected['title']} by {selected['author']}")
        return selected

def main():
    global remembered_title
    print("📚 Welcome to the Book Assistant!")

    # Search and pick book at start
    while not remembered_title:
        book_info_from_search = search_and_select_book()
        if book_info_from_search is None:
            print("Exiting...")
            return

        verified_title = ensure_book_available_and_ingested(book_info_from_search)
        if verified_title:
            remembered_title = verified_title
        else:
            print("Please try another book.")

    print(f"Ready! You can ask questions, request summaries, or ask to continue the story for '{remembered_title}'.")
    print("Type 'exit' or 'quit' to stop.")
    print("To switch books, just mention the new book title, e.g., 'tell me about Moby Dick'.")


    while True:
        user_input = input(" > ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        # DEBUG PRINTS IN MAIN.PY
        print(f"DEBUG MAIN: User input: '{user_input}'")
        print(f"DEBUG MAIN: remembered_title BEFORE orchestrate_request: '{remembered_title}'")
        
        try:
            response, updated_remembered_title = orchestrate_request(user_input, remembered_title)
            remembered_title = updated_remembered_title # Update the global remembered_title

            print("\n🧠 Answer:\n", response)

        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            import traceback # Add traceback for detailed error location
            traceback.print_exc() # Print full traceback
        
        print(f"DEBUG MAIN: remembered_title AFTER orchestrate_request (for next turn): '{remembered_title}'")


if __name__ == "__main__":
    os.makedirs(DATA_FOLDER, exist_ok=True)
    main()