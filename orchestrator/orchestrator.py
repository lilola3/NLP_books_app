from mcp_servers.gutenberg_api import GutenbergAPI
from .llm_gateway import call_llm
from .vector_store import ingest_book, query_book, is_book_ingested

def handle_user_request(task, payload):
    if task == "search":
        return GutenbergAPI.search_books(payload)

    elif task == "download":
        return GutenbergAPI.get_book_text(payload)

    elif task == "summarize":
        title = payload["title"]
        text = payload["text"]

        if not is_book_ingested(title):
            ingest_book(title, text)

        relevant_chunks = query_book(title, f"Summarize the book {title}")
        joined = "\n".join(relevant_chunks)
        prompt = f"Summarize the following book titled '{title}':\n\n{joined}"
        return call_llm(prompt)

    elif task == "question":
        title = payload["title"]
        question = payload["question"]

        relevant_chunks = query_book(title, question)
        joined = "\n".join(relevant_chunks)
        prompt = f"Answer based on the book '{title}':\n\n{joined}\n\nQuestion: {question}"
        return call_llm(prompt)

    elif task == "continue":
        title = payload["title"]
        user_text = payload["text"]
        prompt = f"Continue writing in the style of '{title}' given this paragraph:\n\n{user_text}"
        return call_llm(prompt)

    else:
        return "Unknown task"
