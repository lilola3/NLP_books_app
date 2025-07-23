# NLP_books_app

## Creating a Book Summarization and Q&A NLP Application using LLMs and Vector Databases

This repository contains the code for an interactive Natural Language Processing (NLP) application designed to allow users to search for books from Project Gutenberg, download them, ingest their content into a vector database (ChromaDB), and then perform various NLP tasks like summarization, story continuation, and question-answering using a Local Language Model (LLM).

## Features

* **Book Search:** Find books available on Project Gutenberg by title.
* **On-Demand Book Download & Ingestion:** Automatically downloads and processes book text, splitting it into chunks and generating embeddings for efficient retrieval.
* **Persistent Vector Store (ChromaDB):** Embeddings are stored locally using ChromaDB, so books are ingested only once, speeding up subsequent interactions.
* **LLM Integration:** Utilizes a local Language Model (LLM) through `llama-cpp-python` for generating responses.
* **Interactive Chat Interface:** A Streamlit-powered web application for seamless user interaction.
* **Core NLP Capabilities:**
    * **Summarization:** Get a summary of the currently selected book.
    * **Story Continuation:** Generate the next part of the story based on the last ingested chunk.
    * **Question Answering (RAG):** Ask questions about the book, and the LLM will answer based on retrieved relevant passages (Retrieval Augmented Generation).

## Project Structure
Coding partner
Excellent! A comprehensive README.md is the cornerstone of any shareable project. It makes it easy for others (and your future self!) to understand, set up, and run your application.

Here's a comprehensive README.md for your NLP_books_app, incorporating all the best practices we've discussed.

Markdown

# NLP_books_app

## Creating a Book Summarization and Q&A NLP Application using LLMs and Vector Databases

This repository contains the code for an interactive Natural Language Processing (NLP) application designed to allow users to search for books from Project Gutenberg, download them, ingest their content into a vector database (ChromaDB), and then perform various NLP tasks like summarization, story continuation, and question-answering using a Local Language Model (LLM).

## Features

* **Book Search:** Find books available on Project Gutenberg by title.
* **On-Demand Book Download & Ingestion:** Automatically downloads and processes book text, splitting it into chunks and generating embeddings for efficient retrieval.
* **Persistent Vector Store (ChromaDB):** Embeddings are stored locally using ChromaDB, so books are ingested only once, speeding up subsequent interactions.
* **LLM Integration:** Utilizes a local Language Model (LLM) through `llama-cpp-python` for generating responses.
* **Interactive Chat Interface:** A Streamlit-powered web application for seamless user interaction.
* **Core NLP Capabilities:**
    * **Summarization:** Get a summary of the currently selected book.
    * **Story Continuation:** Generate the next part of the story based on the last ingested chunk.
    * **Question Answering (RAG):** Ask questions about the book, and the LLM will answer based on retrieved relevant passages (Retrieval Augmented Generation).

## Project Structure

NLP_books_app/
├── .gitignore                   # Specifies intentionally untracked files to ignore
├── requirements.txt             # Lists all Python dependencies
├── story_app.py                 # The main Streamlit web application entry point
├── mcp_agents/                  # Contains modular agents for specific tasks
│   ├── init.py
│   ├── gutenberg_api.py         # Handles Project Gutenberg API interactions (search, download)
│   ├── llm_gateway.py           # Interface for interacting with the local LLM
│   └── vector_store.py          # Manages ChromaDB (ingestion, querying, chunk retrieval)
├── orchestrator/                # Orchestrates the flow between different agents
│   ├── init.py
│   ├── orchestrator_agent.py    # Main logic for parsing user intent and coordinating tasks
│   └── prompt.py                # Manages prompt templates for the LLM
├── main.py                      # (If this is a separate backend/CLI entry point, describe its role)
├── models/                      # Directory to store local LLM model files (e.g., .gguf)
│   └── 

## Setup Instructions

Follow these steps to get the application up and running on your local machine.

### 1. Prerequisites

* **Python 3.9+:** Ensure you have a compatible Python version installed. You can download it from [python.org](https://www.python.org/downloads/).
* **Git:** Necessary for cloning the repository. Download from [git-scm.com](https://git-scm.com/).
* **LLM Model File:** You will need to manually download a compatible LLM model file (e.g., in GGUF format for `llama-cpp-python`).
    * **Create a `models/` directory in your project root and place your downloaded `.gguf` file inside it.**