**Languages:** English (this file) · [Português (Brasil)](README.pt-BR.md) · [Español](README.es.md)

# ai-getting-started-exercise

Example code for the “Como começar com IA” page (stage 1: local, CPU, no GPU). It takes a task you would do by hand — read a fictional meeting record and answer three questions — and turns it into a flow that runs end to end and checks the output against a criterion written before you run it.

```
PDF (pypdf) ─> chunks (source + page) ─> embeddings (sentence-transformers) ─> Chroma
                                                                      │
question ─> search ─> answer (Ollama, or extractive with --modo-teste) ─┴─> saida/resultado.json
                                                                            │
                                                       python -m exercicio checar
                                                       python -m exercicio publicar  ─> docs/ (optional GitHub Pages)
```

## What you need

- Linux, macOS or Windows, with Python 3.11 or newer (tested with Python 3.13 on Linux, CPU, no GPU).
- Default path, local and free of charge: Python, Ollama, pypdf, sentence-transformers and Chroma.
- Optional: OpenRouter (an LLM over the network, with your key in an environment variable) and GitHub Pages (to publish the output).
- Internet only to download the embedding model from Hugging Face, the first time; after that the local path runs offline. `--embeddings fake` does not download a model.
- No API key on the default path. If you use OpenRouter, the key belongs only in `OPENROUTER_API_KEY` (the terminal or a `.env` file, which git ignores). Never in the code.

Embedding model (downloaded when you run the code in `e5` mode, into `~/.cache/huggingface`):

| Role | Model | Where to change it |
|---|---|---|
| Embeddings | `intfloat/multilingual-e5-small` | `EXERCICIO_MODELO_EMBEDDINGS` |

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                           # CPU-only PyTorch
pytest -q
```

For the Ollama path, install [Ollama](https://ollama.com), start the service and pull a model (`ollama pull llama3.2` is an example; use whatever you already have).

## How to run

The completion criterion is in `CRITERIO.md` and `criterio.yaml`, written **before** the flow runs. The input is the fictional PDF `dados/ata-reuniao-ficticia.pdf`.

```bash
# fictional document (already in dados/; the script recreates the PDF)
python -m exercicio gerar-pdf

# deterministic test mode (no Ollama and no OpenRouter):
# extractive answer from the retrieved passages
python -m exercicio rodar --modo-teste --checar

# default path, with local Ollama (fails with a clear message if Ollama is not running)
python -m exercicio rodar --llm ollama --modelo llama3.2 --checar

# OpenRouter option (the key comes only from OPENROUTER_API_KEY)
# Paste your key in the terminal, not in a versioned file.
export OPENROUTER_API_KEY=
python -m exercicio rodar --llm openrouter --modelo YOUR_MODEL --checar

# check on its own, if the output already exists
python -m exercicio checar

# optional step: build docs/index.html from the output, for GitHub Pages
python -m exercicio publicar
```

`--modo-teste` is the documented mode when Ollama is not installed: the answer is extractive and deterministic (it copies the closest passage and cites the file and page; if the text does not contain the answer, it abstains). The pytest suite uses this mode and `fake` embeddings, with no network and no model download.

`--embeddings e5` (the default) uses `intfloat/multilingual-e5-small`. `--embeddings fake` uses deterministic vectors, for tests or for a machine without the model in cache.

### The seven steps of the exercise

1. Choose a limited task and an input with no sensitive information (here, the fictional meeting record).
2. Write the expected output and the completion criterion **before** choosing a tool (`CRITERIO.md`).
3. Separate rule steps (read the PDF, split, write the output, check it) from steps that need interpretation (a natural-language answer when an LLM is used).
4. Build the path with the local input and look at the result in the terminal (and, if you want, in `docs/index.html`). The default path does not send anything outside the machine.
5. Run the known case and check it against the criterion: `python -m exercicio checar`.
6. The out-of-document question (“Qual é a taxa de juros do financiamento imobiliário?”) is the case that should fail if the flow makes up an answer; the right behaviour is to abstain.
7. Decide the next change: another model, the OpenRouter mode, or publishing the output on GitHub Pages.

### Configuration

Everything is an environment variable (`exercicio/config.py`) or a flag:

- `EXERCICIO_LLM` — `ollama` (default), `openrouter` or `teste` (the same as `--llm` / `--modo-teste`).
- `EXERCICIO_LLM_MODELO` — the Ollama name or the OpenRouter id (`--modelo`).
- `OLLAMA_URL` — default `http://localhost:11434`.
- `OPENROUTER_API_KEY` — only in the environment, never in a versioned file. `.env.example` lists the variable empty; copy it to `.env` if you want.
- `EXERCICIO_MODELO_EMBEDDINGS`, `EXERCICIO_EMBEDDINGS` (`e5` or `fake`), `EXERCICIO_INDICE`, `EXERCICIO_SAIDA`.

### Publishing the output on GitHub Pages (optional)

1. Run the flow and then `python -m exercicio publicar`. This (re)writes `docs/index.html`.
2. On GitHub, under Settings → Pages, choose GitHub Actions as the source.
3. Run the `Deploy GitHub Pages` workflow by hand (Actions → the workflow → Run workflow). It lives in `.github/workflows/pages.yml` and is triggered only by `workflow_dispatch`: nothing is published on push or on a pull request.

## Tests

```bash
pytest -q
```

The tests build the PDF in a temporary folder, run the flow with `--modo-teste` and `fake` embeddings, check the criterion, mock OpenRouter (no network) and assert that the key is not written to a file. They do not depend on Ollama or on a model download.

## Structure

```
exercicio/
  pdf.py             PDF reading with pypdf, text per page
  chunks.py          splits that keep the source and page, and never cross pages
  embeddings.py      sentence-transformers (e5) or fake vectors
  banco.py           Chroma persisted on disk
  responder.py       extractive answer, Ollama or OpenRouter
  pipeline.py        end-to-end flow
  checar.py          check against criterio.yaml
  publicar.py        builds docs/index.html from the output
  gerar_pdf.py       recreates the fictional PDF
  cli.py             python -m exercicio ...
CRITERIO.md          completion criterion, written before you run the flow
criterio.yaml        the same criterion, read by the checker
dados/               fictional PDF (CC BY 4.0)
docs/                HTML built for GitHub Pages
indice/, saida/      Chroma index and outputs (not in git)
.github/workflows/   pages.yml (workflow_dispatch only)
tests/               pytest
```

## Limits and common mistakes

- On the default path, if Ollama is not running, the flow exits with code 2 and a message that asks for Ollama, `--modo-teste` or OpenRouter. It does not silently switch backends.
- The extractive answer in `--modo-teste` only copies a passage from the document: if the right passage is not at the top of the search, the answer is wrong even if that passage is in the list.
- A PDF with a table or two columns may come out of order in pypdf; check `saida/texto-extraido.txt` before trusting the answer.
- Chunks never cross pages, so the citation stays correct.
- The OpenRouter key must never go into git. If you paste the key into a file, use only `.env` (ignored). `.env.example` stays empty.
- Left out of this version: OCR, crawling, reranking and an interactive screen (those are in the `ia-faca-voce-mesmo-rag` repository).

## Stages

- Stage 0: open the meeting record in a PDF reader and copy the answers by hand, with no written criterion.
- Stage 1 (this repository): a local script that reads the file, answers and checks the output.
- Stage 2 (not included): scheduling, a log on the network, and a comparison between the local path and a path on a server.

## License and attribution

Code under the MIT license (`LICENSE`). The fictional document in `dados/` under CC BY 4.0 (`dados/LICENSE.md`). Downloaded models have the licenses from their Hugging Face pages.

## Limits of this version

- The Ollama and OpenRouter integrations exist in the code. The tests cover test mode and OpenRouter with a mock, with no network. Ollama must be installed and have a pulled model for the default path to be exercised end to end on this machine.
