class Context:
    def __init__(self):
        self.data = {
            "book_title": None,
            "book_id": None,
            "full_text": None,
            "last_query": None,
            "last_result": None,
            "task_history": []
        }

    def update(self, **kwargs):
        self.data.update(kwargs)
        if "task" in kwargs:
            self.data["task_history"].append(kwargs["task"])

    def get(self, key):
        return self.data.get(key)

    def as_dict(self):
        return self.data
