"""Read digital PDFs with pypdf, keeping page numbers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class Page:
    source: str
    page: int
    text: str
    method: str = "pypdf"

    def as_dict(self) -> dict:
        return asdict(self)


def read_pdf(path: Path) -> list[Page]:
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    reader = PdfReader(str(path))
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append(Page(path.name, number, text, "pypdf"))
    if not pages:
        raise ValueError(f"PDF has no pages: {path}")
    return pages