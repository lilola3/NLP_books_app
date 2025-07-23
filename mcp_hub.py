class MCPHub:
    def __init__(self):
        self.registry = {}

    def register(self, name, func):
        self.registry[name] = func

    def call(self, name, *args, **kwargs):
        if name in self.registry:
            return self.registry[name](*args, **kwargs)
        raise Exception(f"Agent '{name}' not found")

    def serve(self):
        print("Serving MCPHub...")

hub = MCPHub()

# Import agent functions and register them here
from mcp_agents.gutenberg_api import GutenbergAPI
from mcp_agents.llm_gateway import call_llm
from mcp_agents.vector_store import ingest_book, query_book, is_book_ingested, get_last_chunk
from mcp_agents.prompt import build_summary_prompt, build_question_prompt, build_continuation_prompt

hub.register("search_books", GutenbergAPI.search_books)
hub.register("download_book", GutenbergAPI.download_book)
hub.register("call_llm", call_llm)
hub.register("ingest_book", ingest_book)
hub.register("query_book", query_book)
hub.register("is_book_ingested", is_book_ingested)
hub.register("get_last_chunk", get_last_chunk)
hub.register("build_summary_prompt", build_summary_prompt)
hub.register("build_question_prompt", build_question_prompt)
hub.register("build_continuation_prompt", build_continuation_prompt)

if __name__ == "__main__":
    hub.serve()
