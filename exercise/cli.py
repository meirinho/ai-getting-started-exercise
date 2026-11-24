"""CLI: python -m exercise <command>."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config
from .answer import LlmUnavailable


def _config_from_args(args) -> Config:
    cfg = Config.from_env()
    if getattr(args, "test_mode", False):
        cfg.llm = "test"
    if getattr(args, "llm", None):
        cfg.llm = args.llm
    if getattr(args, "embeddings", None):
        cfg.embeddings = args.embeddings
    if getattr(args, "pdf", None):
        cfg.pdf = Path(args.pdf)
    if getattr(args, "output", None):
        cfg.output_dir = Path(args.output)
    if getattr(args, "index", None):
        cfg.index_dir = Path(args.index)
    if getattr(args, "criteria", None):
        cfg.criteria = Path(args.criteria)
    if getattr(args, "pages_dir", None):
        cfg.pages_dir = Path(args.pages_dir)
    if getattr(args, "model", None):
        cfg.llm_model = args.model
    return cfg


def cmd_run(args) -> int:
    from . import check, pipeline

    cfg = _config_from_args(args)
    try:
        result = pipeline.run(cfg)
    except LlmUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    count = len(result["questions"])
    print(
        f"Flow complete: {result['page_count']} page(s), "
        f"{result['chunk_count']} chunk(s), {count} question(s). "
        f"LLM={result['llm']}, embeddings={result['embeddings']}."
    )
    print(f"Output: {cfg.output_dir / 'result.json'}")
    if args.check:
        items = check.verify(cfg, result)
        return check.print_report(items)
    return 0


def cmd_check(args) -> int:
    from . import check

    cfg = _config_from_args(args)
    items = check.verify(cfg)
    print(f"CRITERIA: {cfg.criteria}")
    print(f"OUTPUT:   {cfg.output_dir / 'result.json'}")
    print()
    return check.print_report(items)


def cmd_publish(args) -> int:
    from . import publish as publish_module

    cfg = _config_from_args(args)
    path = publish_module.publish(cfg)
    print(f"Page written: {path}")
    return 0


def cmd_generate_pdf(args) -> int:
    from . import generate_pdf

    path = Path(args.pdf) if args.pdf else None
    dest = generate_pdf.generate(path)
    print(f"PDF written: {dest}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m exercise",
        description=(
            "Run the fictional meeting exercise end to end and "
            "check output against the criterion written beforehand."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="read PDF, index, answer, write output")
    run_cmd.add_argument(
        "--test-mode",
        action="store_true",
        help="deterministic extractive answers, no Ollama or OpenRouter",
    )
    run_cmd.add_argument("--llm", choices=["ollama", "openrouter", "test"])
    run_cmd.add_argument("--embeddings", choices=["e5", "fake"])
    run_cmd.add_argument("--model", help="Ollama or OpenRouter model id")
    run_cmd.add_argument("--pdf", help="input PDF path")
    run_cmd.add_argument("--output", help="output directory (default: output/)")
    run_cmd.add_argument("--index", help="Chroma directory (default: index/)")
    run_cmd.add_argument("--criteria", help="criteria YAML file")
    run_cmd.add_argument(
        "--check",
        action="store_true",
        help="verify output against criteria when finished",
    )
    run_cmd.set_defaults(func=cmd_run)

    check_cmd = sub.add_parser("check", help="verify output/result.json against criteria")
    check_cmd.add_argument("--output", help="output directory")
    check_cmd.add_argument("--criteria", help="criteria YAML file")
    check_cmd.set_defaults(func=cmd_check)

    pub = sub.add_parser("publish", help="build docs/index.html from output")
    pub.add_argument("--output", help="output directory")
    pub.add_argument("--pages-dir", help="destination directory (default: docs/)")
    pub.set_defaults(func=cmd_publish)

    pdf_cmd = sub.add_parser("generate-pdf", help="regenerate the sample PDF")
    pdf_cmd.add_argument("--pdf", help="destination path")
    pdf_cmd.set_defaults(func=cmd_generate_pdf)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2