"""Embeddings locais com sentence-transformers (e5) ou vetores falsos determinísticos.

O modo "fake" não baixa modelo e não acessa a rede. Ele existe para os testes
e para rodar o fluxo numa máquina sem o modelo em cache. O modo "e5" usa
intfloat/multilingual-e5-small (prefixos "query: " e "passage: ").
"""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache

import numpy as np

DIM_FAKE = 128


@lru_cache(maxsize=4)
def carregar_e5(nome: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(nome, device="cpu")


def _e5(nome: str) -> bool:
    return "e5" in nome.lower()


def _vetor_fake(texto: str) -> np.ndarray:
    """Hash determinístico de tokens e trigramas; textos parecidos ficam próximos."""
    v = np.zeros(DIM_FAKE, dtype=np.float32)
    s = texto.lower()
    tokens = re.findall(r"\w+", s, flags=re.UNICODE)
    for tok in tokens:
        h = int(hashlib.sha256(f"t:{tok}".encode("utf-8")).hexdigest(), 16)
        v[h % DIM_FAKE] += 1.0
        if len(tok) >= 3:
            for i in range(len(tok) - 2):
                g = tok[i : i + 3]
                h2 = int(hashlib.sha256(f"g:{g}".encode("utf-8")).hexdigest(), 16)
                v[h2 % DIM_FAKE] += 0.4
    n = float(np.linalg.norm(v))
    return v / n if n else v


def embed_trechos(modo: str, textos: list[str], modelo: str = "") -> np.ndarray:
    if not textos:
        dim = DIM_FAKE if modo == "fake" else 384
        return np.zeros((0, dim), dtype=np.float32)
    if modo == "fake":
        return np.stack([_vetor_fake(t) for t in textos])
    pre = "passage: " if _e5(modelo) else ""
    return carregar_e5(modelo).encode(
        [pre + t for t in textos],
        normalize_embeddings=True,
        batch_size=16,
        show_progress_bar=False,
    )


def embed_pergunta(modo: str, pergunta: str, modelo: str = "") -> np.ndarray:
    if modo == "fake":
        return _vetor_fake(pergunta)
    pre = "query: " if _e5(modelo) else ""
    return carregar_e5(modelo).encode(
        [pre + pergunta],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
