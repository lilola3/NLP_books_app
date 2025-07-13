import os
from orchestrator.orchestrator import handle_user_request

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    print("📚 Welcome to the Book Assistant!")
    query = input("🔎 Enter book title or author: ")

    print("\nSearching for books...")
    book_info = handle_user_request("search", query)

    if not book_info:
        print("❌ No books found.")
        return

    print("\nTop Matches:")
    for idx, book in enumerate(book_info[:5], 1):
        title = book['title']
        author = book['authors'][0]['name'] if book['authors'] else "Unknown"
        print(f"{idx}. {title} — {author}")

    choice = input("📘 Enter the number of the book to download: ")
    try:
        choice = int(choice) - 1
        selected_book = book_info[choice]
    except:
        print("❌ Invalid selection.")
        return

    title = selected_book["title"]
    book_path = os.path.join(DATA_DIR, f"{title}.txt")

    if os.path.exists(book_path):
        with open(book_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        print("📂 Loaded book from local storage.")
    else:
        print(f"\n📥 Downloading '{title}'...")
        full_text = handle_user_request("download", selected_book['id'])
        if not full_text:
            print("❌ Failed to download book text.")
            return
        with open(book_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print("✅ Book saved to local storage.")

    while True:
        task = input("\n🛠 Choose task (summarize / continue / question / exit): ").strip().lower()

        if task == "exit":
            print("👋 Exiting the assistant. Goodbye!")
            break

        elif task == "summarize":
            result = handle_user_request("summarize", {
                "text": full_text,
                "title": title
            })
            print("\n📝 Summary:\n", result)

        elif task == "continue":
            user_paragraph = input("✍️ Enter a paragraph to continue in the author's style:\n")
            result = handle_user_request("continue", {
                "text": user_paragraph,
                "title": title
            })
            print("\n➡️ Continuation:\n", result)

        elif task == "question":
            question = input("❓ What would you like to ask about the book?\n")
            result = handle_user_request("question", {
                "question": question,
                "title": title
            })
            print("\n🧠 Answer:\n", result)

        else:
            print("❌ Unknown task. Please choose summarize / continue / question / exit.")

if __name__ == "__main__":
    main()
