"""Chroma vector store persisted on disk (index/ by default)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .chunks import Chunk


@dataclass
class SearchResult:
    id: str
    text: str
    source: str
    page: int
    similarity: float

    def citation(self) -> str:
        return f"{self.source}, p. {self.page}"


def open_store(directory: Path, collection: str = "exercise"):
    directory.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(directory),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(collection, metadata={"hnsw:space": "cosine"})


def add_chunks(collection, chunks: list[Chunk], vectors) -> int:
    if not chunks:
        return 0
    collection.upsert(
        ids=[c.id for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=[list(map(float, v)) for v in vectors],
        metadatas=[c.metadata() for c in chunks],
    )
    return len(chunks)


def search(collection, vector, k: int) -> list[SearchResult]:
    n = min(k, collection.count())
    if n <= 0:
        return []
    result = collection.query(
        query_embeddings=[list(map(float, vector))],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for chunk_id, doc, meta, dist in zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append(
            SearchResult(
                chunk_id,
                doc,
                meta["source"],
                int(meta["page"]),
                1.0 - float(dist),
            )
        )
    return hits