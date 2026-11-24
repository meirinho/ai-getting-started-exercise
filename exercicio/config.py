"""Configuração por variável de ambiente e argumentos da linha de comando."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

MODOS_LLM = ("ollama", "openrouter", "teste")
MODOS_EMBEDDINGS = ("e5", "fake")

MODELO_E5 = "intfloat/multilingual-e5-small"
ABSTENCAO = "Os documentos não trazem essa informação."


def carregar_dotenv(caminho: Path | None = None) -> None:
    """Lê .env se existir, sem sobrescrever o que já está no ambiente.

    Não imprime valores. Linhas vazias e comentários são ignorados.
    """
    arquivo = caminho or (RAIZ / ".env")
    if not arquivo.is_file():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip("'").strip('"')
        if chave and chave not in os.environ:
            os.environ[chave] = valor


@dataclass
class Config:
    pasta_raiz: Path = RAIZ
    pasta_indice: Path = RAIZ / "indice"
    pasta_saida: Path = RAIZ / "saida"
    pdf: Path = RAIZ / "dados" / "ata-reuniao-ficticia.pdf"
    criterio: Path = RAIZ / "criterio.yaml"
    destino_pages: Path = RAIZ / "docs"
    llm: str = "ollama"
    llm_modelo: str = ""
    ollama_url: str = "http://localhost:11434"
    embeddings: str = "e5"
    modelo_embeddings: str = MODELO_E5
    tamanho_chunk: int = 800
    sobreposicao: int = 60
    k_busca: int = 3
    limiar_similaridade: float = 0.35

    @classmethod
    def do_ambiente(cls) -> "Config":
        carregar_dotenv()
        cfg = cls()
        llm = os.environ.get("EXERCICIO_LLM", "").strip().lower()
        if llm:
            cfg.llm = llm
        cfg.llm_modelo = os.environ.get("EXERCICIO_LLM_MODELO", "").strip()
        url = os.environ.get("OLLAMA_URL", "").strip()
        if url:
            cfg.ollama_url = url.rstrip("/")
        emb = os.environ.get("EXERCICIO_EMBEDDINGS", "").strip().lower()
        if emb:
            cfg.embeddings = emb
        modelo = os.environ.get("EXERCICIO_MODELO_EMBEDDINGS", "").strip()
        if modelo:
            cfg.modelo_embeddings = modelo
        indice = os.environ.get("EXERCICIO_INDICE", "").strip()
        if indice:
            cfg.pasta_indice = Path(indice)
        saida = os.environ.get("EXERCICIO_SAIDA", "").strip()
        if saida:
            cfg.pasta_saida = Path(saida)
        return cfg

    def validar(self) -> None:
        if self.llm not in MODOS_LLM:
            raise ValueError(
                f"LLM desconhecido: {self.llm!r}. Use um destes: {', '.join(MODOS_LLM)}."
            )
        if self.embeddings not in MODOS_EMBEDDINGS:
            raise ValueError(
                f"Embeddings desconhecidos: {self.embeddings!r}. Use e5 ou fake."
            )
