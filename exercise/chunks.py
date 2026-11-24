"""Split text into chunks without crossing pages; keep source and page."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from .pdf import Page


@dataclass
class Chunk:
    id: str
    source: str
    page: int
    text: str
    start: int
    end: int

    def metadata(self) -> dict:
        data = asdict(self)
        data.pop("text")
        data.pop("id")
        return data


def _chunk_id(source: str, page: int, start: int) -> str:
    return hashlib.sha1(f"{source}|{page}|{start}".encode()).hexdigest()[:16]


def _adjust_end(text: str, start: int, end: int) -> int:
    if end >= len(text):
        return len(text)
    space = text.rfind(" ", start + 1, end)
    return space if space > start + (end - start) // 2 else end


def _fixed_ranges(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    if size <= 0:
        raise ValueError("size must be greater than zero")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be between 0 and size - 1")
    if not text.strip():
        return []
    if len(text) <= size:
        return [(0, len(text))]
    ranges, start = [], 0
    while start < len(text):
        end = _adjust_end(text, start, start + size)
        ranges.append((start, end))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return ranges


def _paragraph_ranges(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    """Join paragraphs up to size. Long paragraphs fall back to fixed splits."""
    paragraphs = list(re.finditer(r"\S(?:.|\n)*?(?:\n[ \t]*\n|$)", text))
    if not paragraphs:
        return _fixed_ranges(text, size, overlap)
    ranges: list[tuple[int, int]] = []
    acc_start: int | None = None
    acc_end: int | None = None

    def split_long(start: int, end: int) -> None:
        for a, b in _fixed_ranges(text[start:end], size, overlap):
            ranges.append((start + a, start + b))

    for match in paragraphs:
        start, end = match.start(), match.end()
        if acc_start is None:
            if (end - start) > size:
                split_long(start, end)
                acc_start, acc_end = None, None
            else:
                acc_start, acc_end = start, end
            continue
        if (end - acc_start) <= size:
            acc_end = end
            continue
        ranges.append((acc_start, acc_end))
        if (end - start) > size:
            split_long(start, end)
            acc_start, acc_end = None, None
        else:
            acc_start, acc_end = start, end
    if acc_start is not None and acc_end is not None:
        ranges.append((acc_start, acc_end))
    return ranges


def split_pages(pages: list[Page], size: int = 400, overlap: int = 60) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page in pages:
        if not page.text.strip():
            continue
        for start, end in _paragraph_ranges(page.text, size, overlap):
            excerpt = page.text[start:end].strip()
            if not excerpt:
                continue
            chunks.append(
                Chunk(
                    id=_chunk_id(page.source, page.page, start),
                    source=page.source,
                    page=page.page,
                    text=excerpt,
                    start=start,
                    end=end,
                )
            )
    return chunks