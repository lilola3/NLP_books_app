# prompts.py

def build_summary_prompt(title, text_chunk):
    return (
        f"You are a literary expert. Summarize the following book titled '{title}' clearly and concisely.\n\n"
        f"{text_chunk}"
    )

def build_question_prompt(title, context, question):
    return (
        f"You are a helpful AI assistant answering questions about the book '{title}'.\n\n"
        f"Context from the book:\n{context}\n\n"
        f"Question: {question}\n"
        "Answer concisely based only on the provided context."
    )

def build_continuation_prompt(title, last_paragraph):
    return (
        f"You are continuing the book '{title}'.\n\n"
        f"This is the last paragraph of the book:\n{last_paragraph}\n\n"
        "Continue the narrative in the same tone, style, and voice as the original."
    )
