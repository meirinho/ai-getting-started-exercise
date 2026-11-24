"""Verify output/result.json against the criterion written before running."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from .config import ABSTENTION_MESSAGE, Config


def load_criteria(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _item(name: str, passed: bool, detail: str) -> dict:
    return {"id": name, "ok": passed, "detail": detail}


def verify(cfg: Config | None = None, result: dict | None = None) -> list[dict]:
    cfg = cfg or Config.from_env()
    criteria = load_criteria(cfg.criteria)
    items: list[dict] = []

    output_path = cfg.output_dir / "result.json"
    if result is None:
        if not output_path.is_file():
            items.append(_item("output_file", False, f"not found: {output_path}"))
            return items
        result = json.loads(output_path.read_text(encoding="utf-8"))

    by_id = {q["id"]: q for q in result.get("questions") or []}
    required = {"id", "question", "answer"}
    complete = bool(by_id) and all(
        required <= set(q) and {"text", "citations", "abstained", "mode"} <= set(q["answer"])
        for q in result.get("questions") or []
    )
    items.append(
        _item(
            "output_file",
            complete,
            "result.json is complete" if complete else "missing fields in result.json",
        )
    )

    text = result.get("extracted_text") or ""
    anchors = list(criteria.get("anchor_phrases") or [])
    missing = [phrase for phrase in anchors if phrase not in text]
    items.append(
        _item(
            "extracted_text",
            not missing,
            "PDF was read and contains anchor phrases"
            if not missing
            else "missing in extracted text: " + ", ".join(missing),
        )
    )

    abstention = (criteria.get("abstention_message") or ABSTENTION_MESSAGE).lower()
    for entry in criteria.get("questions") or []:
        qid = entry["id"]
        got = by_id.get(qid)
        if not got:
            items.append(_item(qid, False, "question missing from output"))
            continue
        ans = got["answer"]
        answer_text = ans.get("text") or ""
        if entry.get("abstain"):
            passed = bool(ans.get("abstained")) or abstention in answer_text.lower()
            detail = (
                "flow abstained"
                if passed
                else f"should abstain, got: {answer_text!r}"
            )
            items.append(_item(qid, passed, detail))
            continue
        absent = [phrase for phrase in (entry.get("must_contain") or []) if phrase not in answer_text]
        citations = ans.get("citations") or []
        has_citation = (not entry.get("cite")) or bool(citations) or ", p. " in answer_text
        if absent:
            items.append(_item(qid, False, "missing in answer: " + ", ".join(absent)))
        elif not has_citation:
            items.append(_item(qid, False, "answer does not cite file and page"))
        else:
            items.append(_item(qid, True, "contains expected text and cites the source"))
    return items


def print_report(items: list[dict], stream=None) -> int:
    stream = stream or sys.stdout
    failed = 0
    for item in items:
        label = "ok" if item["ok"] else "FAIL"
        line = f"[{label:<6}] {item['id']} — {item['detail']}"
        print(line, file=stream)
        if not item["ok"]:
            failed += 1
    total = len(items)
    print(
        f"\n{total} items checked, {total - failed} ok, {failed} failed.",
        file=stream,
    )
    return 1 if failed or not items else 0