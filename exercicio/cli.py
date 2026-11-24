"""Linha de comando: python -m exercicio <comando>."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config
from .responder import LlmIndisponivel


def _config_dos_args(args) -> Config:
    cfg = Config.do_ambiente()
    if getattr(args, "modo_teste", False):
        cfg.llm = "teste"
    if getattr(args, "llm", None):
        cfg.llm = args.llm
    if getattr(args, "embeddings", None):
        cfg.embeddings = args.embeddings
    if getattr(args, "pdf", None):
        cfg.pdf = Path(args.pdf)
    if getattr(args, "saida", None):
        cfg.pasta_saida = Path(args.saida)
    if getattr(args, "indice", None):
        cfg.pasta_indice = Path(args.indice)
    if getattr(args, "criterio", None):
        cfg.criterio = Path(args.criterio)
    if getattr(args, "destino", None):
        cfg.destino_pages = Path(args.destino)
    if getattr(args, "modelo", None):
        cfg.llm_modelo = args.modelo
    return cfg


def cmd_rodar(args) -> int:
    from . import checar, pipeline

    cfg = _config_dos_args(args)
    try:
        saida = pipeline.rodar(cfg)
    except LlmIndisponivel as e:
        print(str(e), file=sys.stderr)
        return 2
    n = len(saida["perguntas"])
    print(
        f"Fluxo concluído: {saida['n_paginas']} página(s), "
        f"{saida['n_chunks']} chunk(s), {n} pergunta(s). "
        f"LLM={saida['llm']}, embeddings={saida['embeddings']}."
    )
    print(f"Saída: {cfg.pasta_saida / 'resultado.json'}")
    if args.checar:
        itens = checar.conferir(cfg, saida)
        return checar.imprimir(itens)
    return 0


def cmd_checar(args) -> int:
    from . import checar

    cfg = _config_dos_args(args)
    itens = checar.conferir(cfg)
    print(f"CRITÉRIO: {cfg.criterio}")
    print(f"SAÍDA:    {cfg.pasta_saida / 'resultado.json'}")
    print()
    return checar.imprimir(itens)


def cmd_publicar(args) -> int:
    from . import publicar

    cfg = _config_dos_args(args)
    caminho = publicar.publicar(cfg)
    print(f"Página gerada: {caminho}")
    return 0


def cmd_gerar_pdf(args) -> int:
    from . import gerar_pdf

    caminho = Path(args.pdf) if args.pdf else None
    destino = gerar_pdf.gerar(caminho)
    print(f"PDF gerado: {destino}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m exercicio",
        description=(
            "Leva a ata fictícia a um fluxo que roda do começo ao fim "
            "e confere a saída contra o critério escrito antes."
        ),
    )
    sub = p.add_subparsers(dest="comando", required=True)

    rodar = sub.add_parser("rodar", help="lê o PDF, indexa, responde e grava a saída")
    rodar.add_argument(
        "--modo-teste",
        action="store_true",
        help="resposta extrativa determinística, sem Ollama e sem OpenRouter",
    )
    rodar.add_argument("--llm", choices=["ollama", "openrouter", "teste"])
    rodar.add_argument("--embeddings", choices=["e5", "fake"])
    rodar.add_argument("--modelo", help="nome ou id do modelo (Ollama ou OpenRouter)")
    rodar.add_argument("--pdf", help="caminho do PDF de entrada")
    rodar.add_argument("--saida", help="pasta da saída (padrão: saida/)")
    rodar.add_argument("--indice", help="pasta do Chroma (padrão: indice/)")
    rodar.add_argument("--criterio", help="arquivo YAML do critério")
    rodar.add_argument(
        "--checar",
        action="store_true",
        help="confere a saída contra o critério ao terminar",
    )
    rodar.set_defaults(func=cmd_rodar)

    chk = sub.add_parser("checar", help="confere saida/resultado.json contra o critério")
    chk.add_argument("--saida", help="pasta da saída")
    chk.add_argument("--criterio", help="arquivo YAML do critério")
    chk.set_defaults(func=cmd_checar)

    pub = sub.add_parser("publicar", help="gera docs/index.html a partir da saída")
    pub.add_argument("--saida", help="pasta da saída")
    pub.add_argument("--destino", help="pasta de destino (padrão: docs/)")
    pub.set_defaults(func=cmd_publicar)

    pdfp = sub.add_parser("gerar-pdf", help="regenera o PDF fictício de exemplo")
    pdfp.add_argument("--pdf", help="caminho de destino")
    pdfp.set_defaults(func=cmd_gerar_pdf)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 2
