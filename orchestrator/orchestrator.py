from mcp_servers.gutenberg_api import GutenbergAPI
from .llm_gateway import call_llm
from .vector_store import ingest_book, query_book, is_book_ingested, get_last_chunk
from .prompts import build_summary_prompt, build_question_prompt, build_continuation_prompt


 def handle_user_request(task, payload):
    ctx = payload.get("ctx")

    if task == "search":
        return GutenbergAPI.search_books(payload)
    
    elif task == "download":
        return GutenbergAPI.get_book_text(payload)

    elif task == "summarize":
        title = payload["title"]
        text = payload["text"]
        if ctx: ctx.update(task="summarize", book_title=title)

        if not is_book_ingested(title):
            ingest_book(title, text)

        relevant_chunks = query_book(title, f"Summarize the book {title}")
        joined = "\n".join(relevant_chunks)
        prompt = build_summary_prompt(title, joined)
        result = call_llm(prompt)
        if ctx: ctx.update(last_result=result)
        return result

    elif task == "question":
        title = payload["title"]
        question = payload["question"]
        if ctx: ctx.update(task="question", book_title=title, last_query=question)

        relevant_chunks = query_book(title, question)
        joined = "\n".join(relevant_chunks)
        prompt = build_question_prompt(title, joined, question)
        result = call_llm(prompt)
        if ctx: ctx.update(last_result=result)
        return result

    elif task == "continue":
        title = payload["title"]
        text = payload.get("text")
        if ctx: ctx.update(task="continue", book_title=title)

        if not is_book_ingested(title):
            print("📥 Ingesting book first...")
            ingest_book(title, text or "")

        last_chunk = get_last_chunk(title)
        prompt = build_continuation_prompt(title, last_chunk)
        result = call_llm(prompt)
        if ctx: ctx.update(last_result=result)
        return result

    else:
        return "Unknown task"
