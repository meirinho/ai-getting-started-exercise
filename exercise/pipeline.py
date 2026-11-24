"""End-to-end flow: PDF → chunks → embeddings → Chroma → answers → JSON."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import answer, chunks, embeddings, pdf, store
from .config import Config


def load_criteria(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def build_index(cfg: Config) -> dict:
    pages = pdf.read_pdf(cfg.pdf)
    pieces = chunks.split_pages(pages, cfg.chunk_size, cfg.chunk_overlap)
    vectors = embeddings.embed_passages(
        cfg.embeddings, [c.text for c in pieces], cfg.embedding_model
    )
    collection = store.open_store(cfg.index_dir)
    old_ids = collection.get()["ids"]
    if old_ids:
        collection.delete(ids=old_ids)
    count = store.add_chunks(collection, pieces, vectors)
    return {
        "pages": [p.as_dict() for p in pages],
        "page_count": len(pages),
        "chunk_count": count,
    }


def ask(cfg: Config, question: str):
    collection = store.open_store(cfg.index_dir)
    vector = embeddings.embed_query(cfg.embeddings, question, cfg.embedding_model)
    hits = store.search(collection, vector, cfg.search_k)
    return answer.answer_question(question, hits, cfg), hits


def run(cfg: Config) -> dict:
    cfg.validate()
    answer.ensure_backend(cfg)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    criteria = load_criteria(cfg.criteria)
    index = build_index(cfg)
    rows = []
    for entry in criteria["questions"]:
        response, hits = ask(cfg, entry["question"])
        rows.append(
            {
                "id": entry["id"],
                "question": entry["question"],
                "answer": response.as_dict(),
                "passages": [
                    {
                        "source": h.source,
                        "page": h.page,
                        "similarity": round(h.similarity, 4),
                        "text": h.text,
                    }
                    for h in hits
                ],
            }
        )
    output = {
        "criteria": str(cfg.criteria.relative_to(cfg.root_dir))
        if cfg.criteria.is_relative_to(cfg.root_dir)
        else str(cfg.criteria),
        "input": str(cfg.pdf.name),
        "llm": cfg.llm,
        "embeddings": cfg.embeddings,
        "embedding_model": cfg.embedding_model if cfg.embeddings == "e5" else "fake",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "page_count": index["page_count"],
        "chunk_count": index["chunk_count"],
        "extracted_text": "\n\n".join(p["text"] for p in index["pages"]),
        "pages": index["pages"],
        "questions": rows,
    }
    result_path = cfg.output_dir / "result.json"
    result_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text_path = cfg.output_dir / "extracted-text.txt"
    text_path.write_text(output["extracted_text"] + "\n", encoding="utf-8")
    return output