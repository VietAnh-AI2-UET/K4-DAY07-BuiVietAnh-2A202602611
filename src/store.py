from __future__ import annotations

import copy
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._store: list[dict[str, Any]] = []
        self._next_index = 0

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = copy.deepcopy(doc.metadata) if doc.metadata is not None else {}
        metadata["doc_id"] = metadata.get("doc_id", doc.id.split("#")[0] if "#" in doc.id else doc.id)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content)
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_emb = self._embedding_fn(query)
        scored = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            scored.append((score, r))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, r in scored[:top_k]:
            rec = r.copy()
            rec.pop("embedding", None)
            rec["score"] = score
            results.append(rec)
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.
        """
        for d in docs:
            self._store.append(self._make_record(d))

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        records = self._store
        if metadata_filter:
            filtered = []
            for r in records:
                match = True
                for k, v in metadata_filter.items():
                    if r.get("metadata", {}).get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(r)
            records = filtered
            
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        original_len = len(self._store)
        self._store = [r for r in self._store if r.get("metadata", {}).get("doc_id") != doc_id]
        return len(self._store) < original_len
