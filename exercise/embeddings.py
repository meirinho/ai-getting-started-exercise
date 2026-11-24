"""Local embeddings with sentence-transformers (e5) or deterministic fake vectors.

Fake mode avoids downloads and network use (tests and dry runs). E5 mode uses
intfloat/multilingual-e5-small with "query: " and "passage: " prefixes.
"""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import numpy as np

FAKE_DIM = 128


@lru_cache(maxsize=4)
def _load_e5(name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(name, device="cpu")


def _is_e5(name: str) -> bool:
    return "e5" in name.lower()


def _fake_vector(text: str) -> np.ndarray:
    vector = np.zeros(FAKE_DIM, dtype=np.float32)
    lowered = text.lower()
    tokens = re.findall(r"\w+", lowered, flags=re.UNICODE)
    for token in tokens:
        h = int(hashlib.sha256(f"t:{token}".encode("utf-8")).hexdigest(), 16)
        vector[h % FAKE_DIM] += 1.0
        if len(token) >= 3:
            for i in range(len(token) - 2):
                tri = token[i : i + 3]
                h2 = int(hashlib.sha256(f"g:{tri}".encode("utf-8")).hexdigest(), 16)
                vector[h2 % FAKE_DIM] += 0.4
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def embed_passages(mode: str, texts: list[str], model: str = "") -> np.ndarray:
    if not texts:
        dim = FAKE_DIM if mode == "fake" else 384
        return np.zeros((0, dim), dtype=np.float32)
    if mode == "fake":
        return np.stack([_fake_vector(t) for t in texts])
    prefix = "passage: " if _is_e5(model) else ""
    return _load_e5(model).encode(
        [prefix + t for t in texts],
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=False,
    )


def embed_query(mode: str, question: str, model: str = "") -> np.ndarray:
    if mode == "fake":
        return _fake_vector(question)
    prefix = "query: " if _is_e5(model) else ""
    return _load_e5(model).encode(
        [prefix + question],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]