"""Answer from retrieved chunks: test mode, Ollama, or OpenRouter."""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field

import requests

from .config import ABSTENTION_MESSAGE
from .store import SearchResult

STOP = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "no", "na", "nas", "nos",
    "e", "ou", "que", "qual", "quais", "quando", "quem", "como",
    "para", "por", "com", "pelo", "pela", "pelos", "pelas",
    "ao", "à", "aos", "às", "é", "foi", "será", "ser",
    "the", "of", "and", "is", "a", "an",
}


@dataclass
class Answer:
    text: str
    citations: list[str] = field(default_factory=list)
    abstained: bool = False
    mode: str = "test"
    model: str = "extractive-local"

    def as_dict(self) -> dict:
        return asdict(self)


def _tokens(text: str) -> set[str]:
    return {
        t for t in re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        if t not in STOP and len(t) > 2
    }


def _overlap(question: str, chunk: str) -> float:
    q, t = _tokens(question), _tokens(chunk)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)


def extractive(
    question: str, hits: list[SearchResult], threshold: float, embedding_mode: str
) -> Answer:
    if not hits:
        return Answer(ABSTENTION_MESSAGE, [], True, "test", "extractive-local")
    top = hits[0]
    overlap = max(_overlap(question, h.text) for h in hits)
    if overlap < 0.25:
        return Answer(ABSTENTION_MESSAGE, [], True, "test", "extractive-local")
    excerpt = " ".join(top.text.split())
    return Answer(
        f"«{excerpt}» [{top.citation()}]",
        [top.citation()],
        False,
        "test",
        "extractive-local",
    )


def ollama_available(url: str, timeout: float = 2.0) -> bool:
    try:
        response = requests.get(url.rstrip("/") + "/api/tags", timeout=timeout)
        return response.ok
    except (requests.RequestException, OSError):
        return False


class LlmUnavailable(RuntimeError):
    """The requested LLM backend is not available."""


def _ollama_missing_message(url: str) -> str:
    return (
        f"Ollama is not available at {url}. "
        "Install and start Ollama, use --test-mode "
        "(deterministic extractive answers, no LLM), "
        "or set OPENROUTER_API_KEY and use --llm openrouter."
    )


def _openrouter_missing_key_message() -> str:
    return (
        "OpenRouter mode requires the OPENROUTER_API_KEY environment variable "
        "(terminal or .env file, which git ignores; never put the key in code). "
        "Without a key, use --test-mode or --llm ollama."
    )


def _messages(question: str, hits: list[SearchResult]) -> list[dict]:
    context = "\n\n".join(f"[{h.citation()}]\n{h.text}" for h in hits)
    system = (
        "Responda em português do Brasil usando SOMENTE os trechos dados. "
        "Cite o arquivo e a página no formato [arquivo, p. N]. "
        f"Se os trechos não trouxerem a resposta, responda exatamente: {ABSTENTION_MESSAGE}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Trechos:\n{context}\n\nPergunta: {question}"},
    ]


def _parse_answer(text: str, hits: list[SearchResult]) -> Answer:
    text = (text or "").strip()
    abstained = (not text) or (ABSTENTION_MESSAGE.lower() in text.lower())
    if abstained:
        return Answer(ABSTENTION_MESSAGE if not text else text, [], True)
    citations = [h.citation() for h in hits[:1]]
    if hits and hits[0].citation() not in text:
        text = f"{text} [{hits[0].citation()}]"
    return Answer(text, citations, False)


def call_ollama(question: str, hits: list[SearchResult], url: str, model: str) -> Answer:
    if not model:
        raise LlmUnavailable(
            "Ollama mode requires EXERCISE_LLM_MODEL (a model already pulled locally, e.g. llama3.2)."
        )
    if not ollama_available(url):
        raise LlmUnavailable(_ollama_missing_message(url))
    response = requests.post(
        url.rstrip("/") + "/api/chat",
        json={"model": model, "messages": _messages(question, hits), "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    content = (payload.get("message") or {}).get("content") or ""
    answer = _parse_answer(content, hits)
    answer.mode = "ollama"
    answer.model = model
    return answer


def call_openrouter(question: str, hits: list[SearchResult], model: str) -> Answer:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise LlmUnavailable(_openrouter_missing_key_message())
    if not model:
        raise LlmUnavailable("OpenRouter mode requires EXERCISE_LLM_MODEL (model id on OpenRouter).")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": _messages(question, hits)},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    choice = (payload.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content")) or ""
    answer = _parse_answer(content, hits)
    answer.mode = "openrouter"
    answer.model = model
    return answer


def answer_question(question: str, hits: list[SearchResult], cfg) -> Answer:
    if cfg.llm == "test":
        return extractive(question, hits, cfg.similarity_threshold, cfg.embeddings)
    if cfg.llm == "ollama":
        return call_ollama(question, hits, cfg.ollama_url, cfg.llm_model)
    if cfg.llm == "openrouter":
        return call_openrouter(question, hits, cfg.llm_model)
    raise LlmUnavailable(f"Unknown LLM: {cfg.llm}")


def ensure_backend(cfg) -> None:
    """Fail fast before indexing when the requested LLM cannot run."""
    if cfg.llm == "test":
        return
    if cfg.llm == "ollama":
        if not cfg.llm_model:
            raise LlmUnavailable(
                "Ollama mode requires EXERCISE_LLM_MODEL (a model already pulled locally, e.g. llama3.2)."
            )
        if not ollama_available(cfg.ollama_url):
            raise LlmUnavailable(_ollama_missing_message(cfg.ollama_url))
        return
    if cfg.llm == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise LlmUnavailable(_openrouter_missing_key_message())
        if not cfg.llm_model:
            raise LlmUnavailable("OpenRouter mode requires EXERCISE_LLM_MODEL (model id on OpenRouter).")
        return
    raise LlmUnavailable(f"Unknown LLM: {cfg.llm}")