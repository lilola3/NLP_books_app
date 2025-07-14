from llama_cpp import Llama

llm = Llama(model_path="models\capybarahermes-2.5-mistral-7b.Q4_K_M.gguf", n_ctx=2048)

def call_llm(prompt):
    response = llm.create_chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
        stop=["<|end|>", "<|endoftext|>"]
    )
    return response["choices"][0]["message"]["content"].strip()
