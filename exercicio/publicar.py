"""Gera docs/index.html a partir de saida/resultado.json, para o GitHub Pages."""
from __future__ import annotations

import html
import json
from pathlib import Path

from .config import Config


def _esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def renderizar(resultado: dict) -> str:
    perguntas = resultado.get("perguntas") or []
    blocos = []
    for p in perguntas:
        resp = p.get("resposta") or {}
        citas = ", ".join(resp.get("citacoes") or []) or "—"
        absteve = "sim" if resp.get("absteve") else "não"
        blocos.append(
            f"""
<section>
  <h2>{_esc(p.get('id'))}</h2>
  <p><strong>Pergunta.</strong> {_esc(p.get('pergunta'))}</p>
  <p><strong>Resposta.</strong> {_esc(resp.get('texto'))}</p>
  <p><strong>Citações.</strong> {_esc(citas)}</p>
  <p><strong>Absteve.</strong> {_esc(absteve)} · <strong>Modo.</strong> {_esc(resp.get('modo'))}</p>
</section>
"""
        )
    corpo = "\n".join(blocos) or "<p>Nenhuma pergunta na saída.</p>"
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Saída do exercício — ia-como-comecar-exercicio</title>
  <style>
    body {{ font-family: system-ui, sans-serif; line-height: 1.5; max-width: 48rem;
           margin: 2rem auto; padding: 0 1rem; color: #111; }}
    h1, h2 {{ font-weight: 600; }}
    .meta {{ color: #444; }}
    pre {{ white-space: pre-wrap; background: #f5f5f5; padding: 1rem; overflow: auto; }}
  </style>
</head>
<body>
  <h1>Saída do exercício</h1>
  <p class="meta">
    Entrada: {_esc(resultado.get('entrada'))}.
    LLM: {_esc(resultado.get('llm'))}.
    Embeddings: {_esc(resultado.get('embeddings'))}.
    Gerado em (UTC): {_esc(resultado.get('gerado_em'))}.
  </p>
  <p>Conferência contra o critério escrito antes de rodar, em <code>CRITERIO.md</code>
     e <code>criterio.yaml</code>. Esta página é gerada por
     <code>python -m exercicio publicar</code> e pode ser publicada no GitHub Pages
     pelo workflow <code>.github/workflows/pages.yml</code> (disparo manual).</p>
  {corpo}
  <h2>Texto extraído do PDF</h2>
  <pre>{_esc(resultado.get('texto_extraido'))}</pre>
</body>
</html>
"""


def publicar(cfg: Config | None = None) -> Path:
    cfg = cfg or Config.do_ambiente()
    caminho = cfg.pasta_saida / "resultado.json"
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Não achei {caminho}. Rode primeiro: python -m exercicio rodar"
        )
    resultado = json.loads(caminho.read_text(encoding="utf-8"))
    destino = cfg.destino_pages
    destino.mkdir(parents=True, exist_ok=True)
    index = destino / "index.html"
    index.write_text(renderizar(resultado), encoding="utf-8")
    return index
