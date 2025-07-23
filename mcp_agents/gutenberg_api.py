# mcp_agents/gutenberg_api.py

import os
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re 

# Ensure these imports are correct relative to your project structure
# from .vector_store import get_book_path, is_book_downloaded # These imports are not used directly in GutenbergAPI class
# They are used in orchestrator_agent which calls GutenbergAPI methods,
# so we don't need them here to fix the current error.

GUTENBERG_SEARCH_URL = "https://www.gutenberg.org/ebooks/search/?query="
GUTENBERG_BASE_URL = "https://www.gutenberg.org"

# --- NEW: Configure Session with Retries ---
def requests_retry_session(
    retries=5,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 503, 504), # HTTP statuses to retry on
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(['GET', 'POST']) # Only retry GET and POST
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Create a global session for the GutenbergAPI to reuse connections and retry logic
gutenberg_session = requests_retry_session()
# --- END NEW ---

class GutenbergAPI:

    @staticmethod
    def search_books(payload: dict) -> list[dict]:
        title = payload.get("title")
        if not title:
            return []

        query_url = GUTENBERG_SEARCH_URL + title.replace(" ", "+")
        
        try:
            response = gutenberg_session.get(query_url, timeout=10) # Added timeout
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

            soup = BeautifulSoup(response.text, "html.parser")
            books = []

            for li in soup.select("li.booklink")[:10]:  # limit to top 10
                title_tag = li.select_one("span.title")
                author_tag = li.select_one("span.subtitle")
                link_tag = li.select_one("a.link")

                if not title_tag or not link_tag:
                    continue

                title_text = title_tag.text.strip()
                author_text = author_tag.text.strip() if author_tag else "Unknown"
                href = link_tag.get("href")

                book_id = None
                if href and href.startswith("/ebooks/"):
                    # Extract book id, ensuring it's just the number
                    match = re.search(r'/ebooks/(\d+)', href)
                    if match:
                        book_id = match.group(1)

                books.append({
                    "title": title_text,
                    "author": author_text,
                    "link": GUTENBERG_BASE_URL + href,
                    "gutenberg_id": book_id # Renamed 'id' to 'gutenberg_id' for clarity
                })

            return books
        except requests.exceptions.RequestException as e:
            print(f"Network error during search: {e}")
            return []
        except Exception as e:
            print(f"Error parsing search results: {e}")
            return []

    @staticmethod
    def download_book(book_id: int) -> str | None: # Changed input from dict to book_id directly for clarity as per orchestrator's usage
        """
        Downloads the plain text content of a Project Gutenberg book by its ID.
        Returns the raw text content or None on failure.
        """
        if not isinstance(book_id, int):
            try:
                book_id = int(book_id)
            except (ValueError, TypeError):
                print(f"Invalid Gutenberg ID: {book_id}. Must be an integer.")
                return None

        # Project Gutenberg's primary text format URL structure:
        # https://www.gutenberg.org/files/{ID}/{ID}-0.txt
        text_url = f"{GUTENBERG_BASE_URL}/files/{book_id}/{book_id}-0.txt"
        
        try:
            print(f"Attempting direct download from: {text_url}")
            response = gutenberg_session.get(text_url, timeout=60) # Longer timeout for download
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            
            # Check if the content type is text/plain, otherwise it might be an error page
            if 'text/plain' not in response.headers.get('Content-Type', ''):
                print(f"Warning: Unexpected content type for {book_id}: {response.headers.get('Content-Type')}. Content might not be plain text.")
                # You might want to parse for error messages here if necessary.
                # For now, we'll assume a non-text/plain response is a failure.
                return None 

            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Network error during download of book ID {book_id}: {e}")
            return None
        except Exception as e:
            print(f"Error during direct download or processing of book ID {book_id}: {e}")
            return None

    @staticmethod
    def get_book_details(gutenberg_id: int) -> dict | None:
        # This static method is currently not used in your orchestrator,
        # and search_books should provide enough initial details.
        # Keeping it here for completeness but returning None as it's complex to scrape fully.
        print(f"Note: GutenbergAPI.get_book_details for ID {gutenberg_id} called, but its implementation needs to fetch from the book's main page.")
        # If you truly need more details than search_books provides for a specific ID,
        # you'd scrape from f"{GUTENBERG_BASE_URL}/ebooks/{gutenberg_id}"
        # For now, it returns None.
        return None