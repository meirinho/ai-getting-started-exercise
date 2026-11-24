**Languages:** English (this file) · [Português (Brasil)](README.pt-BR.md) · [Español](README.es.md)

# AI Getting Started Exercise

Example code for the “getting started with AI” page (stage 1: local, CPU, no GPU). It takes a task you would do by hand — read a fictional meeting record and answer three questions — and turns it into a flow that runs end to end and checks the output against a criterion written before you run it.

```
PDF (pypdf) ─> chunks (source + page) ─> embeddings (sentence-transformers) ─> Chroma
                                                                      │
question ─> search ─> answer (Ollama, or extractive with --test-mode) ─┴─> output/result.json
                                                                            │
                                                       python -m exercise check
                                                       python -m exercise publish  ─> docs/ (optional GitHub Pages)
```

## What you need

- Linux, macOS or Windows, with Python 3.11 or newer (tested with Python 3.13 on Linux, CPU, no GPU).
- Default path, local and free of charge: Python, Ollama, pypdf, sentence-transformers and Chroma.
- Optional: OpenRouter, GitHub Pages, Docker Compose.
- Internet only to download the embedding model from Hugging Face the first time; after that the local path runs offline. `--embeddings fake` does not download a model.
- No API key on the default path. OpenRouter keys belong only in `OPENROUTER_API_KEY` (terminal or git-ignored `.env`).

| Role | Model | Where to change it |
|---|---|---|
| Embeddings | `intfloat/multilingual-e5-small` | `EXERCISE_EMBEDDING_MODEL` |

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

For Ollama, install [Ollama](https://ollama.com), start the service, and pull a model (for example `ollama pull llama3.2`).

## How to run

The completion criterion is in `CRITERIA.md` and `criteria.yaml`, written **before** the flow runs. The input is `data/fictional-meeting-minutes.pdf`.

```bash
python -m exercise generate-pdf
python -m exercise run --test-mode --check
python -m exercise run --llm ollama --model llama3.2 --check
export OPENROUTER_API_KEY=
python -m exercise run --llm openrouter --model YOUR_MODEL --check
python -m exercise check
python -m exercise publish
```

### Configuration

Environment variables (`exercise/config.py`) or CLI flags:

- `EXERCISE_LLM` — `ollama` (default), `openrouter`, or `test` (same as `--llm` / `--test-mode`).
- `EXERCISE_LLM_MODEL` — Ollama name or OpenRouter id (`--model`).
- `OLLAMA_URL` — default `http://localhost:11434`.
- `OPENROUTER_API_KEY` — environment only.
- `EXERCISE_EMBEDDING_MODEL`, `EXERCISE_EMBEDDINGS` (`e5` or `fake`), `EXERCISE_INDEX`, `EXERCISE_OUTPUT`.

## With Docker

```bash
docker compose up --build
docker compose run --rm --no-deps exercise python -m exercise run --llm ollama --model qwen2.5:1.5b --check
docker compose run --rm --no-deps exercise python -m exercise run --test-mode --check
docker compose run --rm --no-deps exercise pytest -q
```

Default Ollama model in Compose: `qwen2.5:1.5b` via `EXERCISE_LLM_MODEL`. Host folders: `output/`, `index/`.

## Tests

```bash
pytest -q
```

## Structure

```
exercise/     pipeline package (python -m exercise)
data/         fictional PDF (CC BY 4.0)
criteria.yaml criterion read by check
docs/         HTML for GitHub Pages
index/        Chroma store (git-ignored)
output/       JSON output (git-ignored)
```

## License

Code: MIT (`LICENSE`). Fictional PDF: CC BY 4.0 (`data/LICENSE.md`).