# mcp_agents/prompt.py

import json
from mcp_agents.llm_gateway import call_llm

def build_summary_prompt(title: str, chunks: list[str]) -> str:
    """
    Build a prompt for summarizing a book from given chunks.
    """
    context = "\n\n".join(chunks) if chunks else "[No content available]"
    return f"""You are a literary analyst. Summarize the book titled '{title}' using the following excerpts.
Focus on characters, plot, tone, and themes. Avoid boilerplate or meta information.

--- Begin Excerpts ---
{context}
--- End Excerpts ---

Summary:
"""


def build_continuation_prompt(title: str, last_chunk: str) -> str:
    """
    Build a prompt for story continuation based on the last paragraph.
    """
    return f"""You are a literary assistant continuing a novel in the voice of its original author.

Book Title: {title}

Continue the story from the paragraph below. Write 2–3 vivid, descriptive paragraphs that follow naturally and stay in character.

Previous paragraph:
\"\"\"{last_chunk}\"\"\"

Next part of the story:
"""


def build_question_prompt(title: str, context: str, user_input: str) -> str:
    """
    Build a prompt to answer a user’s question about a book, using provided context.
    """
    context_text = context if context else "[No relevant context found]"
    return f"""You are a helpful literary assistant. Use the provided context from the book '{title}' to answer the user's question.

Context:
{context_text}

Question:
{user_input}

Answer (based only on the text above, do not guess beyond it):
"""


def parse_intent_and_title(user_input: str, current_book_title: str = None) -> dict:
    # DEBUG PRINT AT START OF FUNCTION
    print(f"DEBUG PROMPT: parse_intent_and_title called with current_book_title: '{current_book_title}'")

    prompt = f"""
You are a helpful assistant that extracts the user's intent and, if a new book is explicitly mentioned, the book title they are asking about.

**Strict Rule:** If the user clearly mentions a book title that is *different* from the `Current active book`, the `intent` MUST be `"switch_book"`, and the `title` MUST be the new book's title. Otherwise, the intent should be based on the action requested (question, summary, continuation).

User input: "{user_input}"
Current active book: "{current_book_title if current_book_title else 'None'}"

Return a JSON object with two fields:
- intent: one of ["question", "summary", "continuation", "switch_book"]
- title: the book title mentioned by the user (string), or null if no *new* book title is explicitly mentioned.

Examples:
Input: "Who are the characters in Pride and Prejudice?"
Current active book: "None"
Output: {{ "intent": "question", "title": "Pride and Prejudice" }}

Input: "Can you summarize Crime and Punishment?"
Current active book: "A Tale of Two Cities"
Output: {{ "intent": "switch_book", "title": "Crime and Punishment" }}

Input: "What happens next in Dracula?"
Current active book: "Dracula"
Output: {{ "intent": "continuation", "title": null }}

Input: "Tell me about Moby Dick instead."
Current active book: "Pride and Prejudice"
Output: {{ "intent": "switch_book", "title": "Moby Dick" }}

Input: "summarize"
Current active book: "Frankenstein"
Output: {{ "intent": "summary", "title": null }}

Input: "who is scrooge"
Current active book: "A Christmas Carol"
Output: {{ "intent": "question", "title": null }}

Now analyze the user input and provide only the JSON output.
"""
    response = call_llm(prompt)

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        json_str = response[start:end]
        result = json.loads(json_str)
    except Exception:
        print(f"Warning: Could not parse LLM response to JSON: {response}")
        result = {"intent": "question", "title": None} # Fallback

    # Basic validation
    valid_intents = ("question", "summary", "continuation", "switch_book")
    if result.get("intent") not in valid_intents:
        result["intent"] = "question" # Default to question if intent is unknown

    extracted_title_lower = result.get("title", "").lower().strip()
    # THIS LINE IS CRITICAL - ENSURE IT HAS THE GUARD
    current_book_title_lower = (current_book_title.lower().strip() if current_book_title else '')

    # Calculate is_same_book_by_contains unconditionally if there's an extracted title
    is_same_book_by_contains = False # Initialize to False
    if extracted_title_lower:
        is_same_book_by_contains = (extracted_title_lower in current_book_title_lower) or \
                                   (current_book_title_lower and current_book_title_lower in extracted_title_lower)
    
    # Force 'switch_book' intent if a genuinely new/different title is detected by string comparison
    if extracted_title_lower and not is_same_book_by_contains:
        if result["intent"] != "switch_book":
            print(f"Debug: Forcing 'switch_book' intent for new title '{result['title']}' vs current '{current_book_title}'")
            result["intent"] = "switch_book"
    
    # If the LLM returned a title that IS the current book (or similar variant), set it to None
    # This prevents `orchestrate_request` from trying to switch to the same book.
    # This should only happen if the user isn't explicitly trying to switch (intent != "switch_book").
    if extracted_title_lower and is_same_book_by_contains and result["intent"] != "switch_book":
        result["title"] = None # Clear the title, as it's not a new book

    # If the intent is switch_book but no title was extracted (e.g., "switch books"), keep title as None
    if result.get("intent") == "switch_book" and not result.get("title"):
         result["title"] = None

    return result