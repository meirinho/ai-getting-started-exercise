"""Banco vetorial Chroma persistido em disco (pasta indice/ por padrão)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .chunks import Chunk


@dataclass
class Resultado:
    id: str
    texto: str
    fonte: str
    pagina: int
    similaridade: float

    def citacao(self) -> str:
        return f"{self.fonte}, p. {self.pagina}"


def abrir(pasta: Path, colecao: str = "exercicio"):
    pasta.mkdir(parents=True, exist_ok=True)
    cliente = chromadb.PersistentClient(
        path=str(pasta),
        settings=Settings(anonymized_telemetry=False),
    )
    return cliente.get_or_create_collection(colecao, metadata={"hnsw:space": "cosine"})


def adicionar(col, chunks: list[Chunk], vetores) -> int:
    if not chunks:
        return 0
    col.upsert(
        ids=[c.id for c in chunks],
        documents=[c.texto for c in chunks],
        embeddings=[list(map(float, v)) for v in vetores],
        metadatas=[c.metadados() for c in chunks],
    )
    return len(chunks)


def buscar(col, vetor, k: int) -> list[Resultado]:
    n = min(k, col.count())
    if n <= 0:
        return []
    r = col.query(
        query_embeddings=[list(map(float, vetor))],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    saida = []
    for i, doc, meta, dist in zip(
        r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0]
    ):
        saida.append(
            Resultado(
                i,
                doc,
                meta["fonte"],
                int(meta["pagina"]),
                1.0 - float(dist),
            )
        )
    return saida
