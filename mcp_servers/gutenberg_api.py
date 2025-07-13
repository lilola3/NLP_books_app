import requests

class GutenbergAPI:
    BASE_URL = "https://gutendex.com/books/"

    @staticmethod
    def search_books(query):
        url = f"{GutenbergAPI.BASE_URL}?search={query}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("results", [])

    @staticmethod
    def get_book_text(book_id):
        url = f"https://gutendex.com/books/{book_id}"
        response = requests.get(url)
        data = response.json()

        formats = data.get("formats", {})
        text_url = formats.get("text/plain; charset=utf-8") or \
                   formats.get("text/plain") or \
                   formats.get("text/plain; charset=us-ascii")

        if not text_url:
            print("❌ No plain text version available for this book.")
            return None

        try:
            text_response = requests.get(text_url)
            return text_response.text
        except Exception as e:
            print(f"❌ Error downloading book text: {e}")
            return None
