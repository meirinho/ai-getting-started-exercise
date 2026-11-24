"""Configuration from environment variables and CLI flags."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LLM_MODES = ("ollama", "openrouter", "test")
EMBEDDING_MODES = ("e5", "fake")

E5_MODEL = "intfloat/multilingual-e5-small"
# Portuguese abstention phrase (exercise fixture text, not UI copy).
ABSTENTION_MESSAGE = "Os documentos não trazem essa informação."


def load_dotenv(path: Path | None = None) -> None:
    """Load .env when present without overriding existing environment."""
    file_path = path or (ROOT / ".env")
    if not file_path.is_file():
        return
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class Config:
    root_dir: Path = ROOT
    index_dir: Path = ROOT / "index"
    output_dir: Path = ROOT / "output"
    pdf: Path = ROOT / "data" / "fictional-meeting-minutes.pdf"
    criteria: Path = ROOT / "criteria.yaml"
    pages_dir: Path = ROOT / "docs"
    llm: str = "ollama"
    llm_model: str = ""
    ollama_url: str = "http://localhost:11434"
    embeddings: str = "e5"
    embedding_model: str = E5_MODEL
    chunk_size: int = 800
    chunk_overlap: int = 60
    search_k: int = 3
    similarity_threshold: float = 0.35

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        cfg = cls()
        llm = os.environ.get("EXERCISE_LLM", "").strip().lower()
        if llm:
            cfg.llm = llm
        cfg.llm_model = os.environ.get("EXERCISE_LLM_MODEL", "").strip()
        url = os.environ.get("OLLAMA_URL", "").strip()
        if url:
            cfg.ollama_url = url.rstrip("/")
        emb = os.environ.get("EXERCISE_EMBEDDINGS", "").strip().lower()
        if emb:
            cfg.embeddings = emb
        model = os.environ.get("EXERCISE_EMBEDDING_MODEL", "").strip()
        if model:
            cfg.embedding_model = model
        index = os.environ.get("EXERCISE_INDEX", "").strip()
        if index:
            cfg.index_dir = Path(index)
        output = os.environ.get("EXERCISE_OUTPUT", "").strip()
        if output:
            cfg.output_dir = Path(output)
        return cfg

    def validate(self) -> None:
        if self.llm not in LLM_MODES:
            raise ValueError(
                f"Unknown LLM {self.llm!r}. Use one of: {', '.join(LLM_MODES)}."
            )
        if self.embeddings not in EMBEDDING_MODES:
            raise ValueError(
                f"Unknown embeddings mode {self.embeddings!r}. Use e5 or fake."
            )