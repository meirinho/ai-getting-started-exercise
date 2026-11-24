"""Fluxo de ponta a ponta: PDF → chunks → embeddings → Chroma → respostas → JSON."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import banco, chunks, embeddings, pdf, responder
from .config import Config


def carregar_criterio(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def indexar(cfg: Config) -> dict:
    paginas = pdf.ler_pdf(cfg.pdf)
    pedacos = chunks.cortar(paginas, cfg.tamanho_chunk, cfg.sobreposicao)
    vetores = embeddings.embed_trechos(
        cfg.embeddings, [c.texto for c in pedacos], cfg.modelo_embeddings
    )
    col = banco.abrir(cfg.pasta_indice)
    ids_antigos = col.get()["ids"]
    if ids_antigos:
        col.delete(ids=ids_antigos)
    n = banco.adicionar(col, pedacos, vetores)
    return {
        "paginas": [p.como_dict() for p in paginas],
        "n_paginas": len(paginas),
        "n_chunks": n,
    }


def perguntar(cfg: Config, pergunta: str):
    col = banco.abrir(cfg.pasta_indice)
    vetor = embeddings.embed_pergunta(cfg.embeddings, pergunta, cfg.modelo_embeddings)
    resultados = banco.buscar(col, vetor, cfg.k_busca)
    return responder.responder(pergunta, resultados, cfg), resultados


def rodar(cfg: Config) -> dict:
    cfg.validar()
    responder.garantir_backend(cfg)
    cfg.pasta_saida.mkdir(parents=True, exist_ok=True)
    criterio = carregar_criterio(cfg.criterio)
    indice = indexar(cfg)
    itens = []
    for item in criterio["perguntas"]:
        resp, resultados = perguntar(cfg, item["pergunta"])
        itens.append(
            {
                "id": item["id"],
                "pergunta": item["pergunta"],
                "resposta": resp.como_dict(),
                "trechos": [
                    {
                        "fonte": r.fonte,
                        "pagina": r.pagina,
                        "similaridade": round(r.similaridade, 4),
                        "texto": r.texto,
                    }
                    for r in resultados
                ],
            }
        )
    saida = {
        "criterio": str(cfg.criterio.relative_to(cfg.pasta_raiz))
        if cfg.criterio.is_relative_to(cfg.pasta_raiz)
        else str(cfg.criterio),
        "entrada": str(cfg.pdf.name),
        "llm": cfg.llm,
        "embeddings": cfg.embeddings,
        "modelo_embeddings": cfg.modelo_embeddings if cfg.embeddings == "e5" else "fake",
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_paginas": indice["n_paginas"],
        "n_chunks": indice["n_chunks"],
        "texto_extraido": "\n\n".join(p["texto"] for p in indice["paginas"]),
        "paginas": indice["paginas"],
        "perguntas": itens,
    }
    caminho = cfg.pasta_saida / "resultado.json"
    caminho.write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    texto_path = cfg.pasta_saida / "texto-extraido.txt"
    texto_path.write_text(saida["texto_extraido"] + "\n", encoding="utf-8")
    return saida
