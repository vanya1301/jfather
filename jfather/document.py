"""Document model and multi-document manager."""

import os

from . import jsontools


class Document:
    """A single JSON document with its own isolated UI state."""

    def __init__(self, text="", path=None, name=None):
        self.text = text
        self.path = path
        self.name = name or (os.path.basename(path) if path else "untitled")
        self.dirty = False
        self.query_rows = []
        self.search_term = ""
        self.expanded_paths = set()

    def set_text(self, text):
        if text != self.text:
            self.text = text
            self.dirty = True

    def parsed(self):
        """Parse this document's text. Raises json.JSONDecodeError."""
        return jsontools.parse(self.text)

    def mark_saved(self, path=None):
        if path is not None:
            self.path = path
            self.name = os.path.basename(path)
        self.dirty = False


class DocumentManager:
    """Holds the list of open documents and the active selection."""

    def __init__(self):
        self.documents = []
        self.active_index = -1

    @property
    def active(self):
        if 0 <= self.active_index < len(self.documents):
            return self.documents[self.active_index]
        return None

    def new(self, text="", name=None):
        doc = Document(text=text, name=name)
        self.documents.append(doc)
        self.active_index = len(self.documents) - 1
        return doc

    def open(self, path):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        doc = Document(text=text, path=path)
        self.documents.append(doc)
        self.active_index = len(self.documents) - 1
        return doc

    def switch(self, index):
        if 0 <= index < len(self.documents):
            self.active_index = index
        return self.active

    def close(self, index):
        if not (0 <= index < len(self.documents)):
            return self.active
        del self.documents[index]
        if not self.documents:
            self.active_index = -1
        elif index < self.active_index:
            self.active_index -= 1
        elif self.active_index >= len(self.documents):
            self.active_index = len(self.documents) - 1
        return self.active
