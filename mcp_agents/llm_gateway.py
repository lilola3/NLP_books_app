from llama_cpp import Llama

llm = Llama(model_path="models/capybarahermes-2.5-mistral-7b.Q4_K_M.gguf", n_ctx=2048)

def call_llm(prompt: str) -> str:
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    return response["choices"][0]["message"]["content"].strip()

def call_llm_for_title_extraction(user_input: str) -> str:
    prompt = f"What is the book title mentioned here: '{user_input}'? Only return the book name. If none, say 'None'."
    response = call_llm(prompt)
    return response.strip() if response else None

def call_llm_for_intent_classification(user_input: str) -> str:
    prompt = f"""Classify the user's intent in this message: '{user_input}'
Your answer must be one of: question, summary, continue, unknown.
Only return one word."""
    response = call_llm(prompt)
    return response.strip().lower() if response else "unknown"
