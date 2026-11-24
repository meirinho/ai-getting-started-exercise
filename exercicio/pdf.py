"""Leitura de PDF digital com pypdf, guardando o número da página."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class Pagina:
    fonte: str
    pagina: int
    texto: str
    metodo: str = "pypdf"

    def como_dict(self) -> dict:
        return asdict(self)


def ler_pdf(caminho: Path) -> list[Pagina]:
    if not caminho.is_file():
        raise FileNotFoundError(f"PDF não encontrado: {caminho}")
    leitor = PdfReader(str(caminho))
    paginas = []
    for n, pagina in enumerate(leitor.pages, start=1):
        texto = (pagina.extract_text() or "").strip()
        paginas.append(Pagina(caminho.name, n, texto, "pypdf"))
    if not paginas:
        raise ValueError(f"O PDF não tem páginas: {caminho}")
    return paginas
