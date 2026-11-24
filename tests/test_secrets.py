import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".venv", "__pycache__", ".git", ".pytest_cache", "index", "output"}


def _iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        yield path


def test_env_example_has_empty_key():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY=" in text
    for line in text.splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            assert line.strip() == "OPENROUTER_API_KEY="


def test_no_versioned_file_contains_api_key():
    for path in _iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            match = re.match(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*)$", line)
            if not match or line.strip().startswith("#"):
                continue
            value = match.group(1).split("#", 1)[0].strip().strip("'").strip('"')
            assert value == "", f"value in {path}: {line!r}"