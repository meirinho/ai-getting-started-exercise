import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ["EXERCISE_LLM"] = "test"
os.environ["EXERCISE_EMBEDDINGS"] = "fake"
os.environ.pop("OPENROUTER_API_KEY", None)

from exercise.config import Config  # noqa: E402
from exercise.generate_pdf import generate  # noqa: E402


@pytest.fixture
def workspace(tmp_path) -> Path:
    return tmp_path


@pytest.fixture
def pdf_sample(tmp_path) -> Path:
    dest = tmp_path / "fictional-meeting-minutes.pdf"
    return generate(dest)


@pytest.fixture
def cfg(tmp_path, pdf_sample) -> Config:
    cfg = Config.from_env()
    cfg.root_dir = ROOT
    cfg.pdf = pdf_sample
    cfg.criteria = ROOT / "criteria.yaml"
    cfg.index_dir = tmp_path / "index"
    cfg.output_dir = tmp_path / "output"
    cfg.pages_dir = tmp_path / "docs"
    cfg.llm = "test"
    cfg.embeddings = "fake"
    return cfg