import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
# Os testes nunca chamam um LLM nem baixam modelo.
os.environ["EXERCICIO_LLM"] = "teste"
os.environ["EXERCICIO_EMBEDDINGS"] = "fake"
os.environ.pop("OPENROUTER_API_KEY", None)

from exercicio.config import Config  # noqa: E402
from exercicio.gerar_pdf import gerar  # noqa: E402


@pytest.fixture
def pasta(tmp_path) -> Path:
    return tmp_path


@pytest.fixture
def pdf_exemplo(tmp_path) -> Path:
    destino = tmp_path / "ata-reuniao-ficticia.pdf"
    return gerar(destino)


@pytest.fixture
def cfg(tmp_path, pdf_exemplo) -> Config:
    cfg = Config.do_ambiente()
    cfg.pasta_raiz = RAIZ
    cfg.pdf = pdf_exemplo
    cfg.criterio = RAIZ / "criterio.yaml"
    cfg.pasta_indice = tmp_path / "indice"
    cfg.pasta_saida = tmp_path / "saida"
    cfg.destino_pages = tmp_path / "docs"
    cfg.llm = "teste"
    cfg.embeddings = "fake"
    return cfg
