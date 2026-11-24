"""Confere saida/resultado.json contra o critério escrito antes de rodar."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from .config import ABSTENCAO, Config


def carregar_criterio(caminho: Path) -> dict:
    with caminho.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ok(nome: str, passou: bool, detalhe: str) -> dict:
    return {"id": nome, "ok": passou, "detalhe": detalhe}


def conferir(cfg: Config | None = None, resultado: dict | None = None) -> list[dict]:
    cfg = cfg or Config.do_ambiente()
    criterio = carregar_criterio(cfg.criterio)
    itens: list[dict] = []

    caminho_saida = cfg.pasta_saida / "resultado.json"
    if resultado is None:
        if not caminho_saida.is_file():
            itens.append(_ok("arquivo_saida", False, f"não encontrado: {caminho_saida}"))
            return itens
        resultado = json.loads(caminho_saida.read_text(encoding="utf-8"))

    perguntas = {p["id"]: p for p in resultado.get("perguntas") or []}
    obrigatorias = {"id", "pergunta", "resposta"}
    completo = bool(perguntas) and all(
        obrigatorias <= set(p) and {"texto", "citacoes", "absteve", "modo"} <= set(p["resposta"])
        for p in resultado.get("perguntas") or []
    )
    itens.append(
        _ok(
            "arquivo_saida",
            completo,
            "resultado.json está completo" if completo else "faltam campos em resultado.json",
        )
    )

    texto = resultado.get("texto_extraido") or ""
    ancora = list(criterio.get("frases_ancora") or [])
    faltando = [f for f in ancora if f not in texto]
    itens.append(
        _ok(
            "texto_extraido",
            not faltando,
            "o PDF foi lido e contém as frases âncora"
            if not faltando
            else "faltam no texto extraído: " + ", ".join(faltando),
        )
    )

    abstencao = (criterio.get("mensagem_abstencao") or ABSTENCAO).lower()
    for item in criterio.get("perguntas") or []:
        ident = item["id"]
        obtido = perguntas.get(ident)
        if not obtido:
            itens.append(_ok(ident, False, "pergunta ausente na saída"))
            continue
        resp = obtido["resposta"]
        texto_resp = resp.get("texto") or ""
        if item.get("abstencao"):
            passou = bool(resp.get("absteve")) or abstencao in texto_resp.lower()
            detalhe = (
                "o fluxo se absteve"
                if passou
                else f"deveria se abster, resposta foi: {texto_resp!r}"
            )
            itens.append(_ok(ident, passou, detalhe))
            continue
        faltam = [f for f in (item.get("deve_conter") or []) if f not in texto_resp]
        citacoes = resp.get("citacoes") or []
        tem_citacao = (not item.get("citar")) or bool(citacoes) or ", p. " in texto_resp
        if faltam:
            itens.append(_ok(ident, False, "faltam na resposta: " + ", ".join(faltam)))
        elif not tem_citacao:
            itens.append(_ok(ident, False, "a resposta não cita o arquivo e a página"))
        else:
            itens.append(_ok(ident, True, "contém o esperado e cita a fonte"))
    return itens


def imprimir(itens: list[dict], destino=None) -> int:
    destino = destino or sys.stdout
    falhou = 0
    for item in itens:
        marca = "ok" if item["ok"] else "FALHOU"
        linha = f"[{marca:<6}] {item['id']} — {item['detalhe']}"
        print(linha, file=destino)
        if not item["ok"]:
            falhou += 1
    total = len(itens)
    print(
        f"\n{total} itens conferidos, {total - falhou} ok, {falhou} falhou.",
        file=destino,
    )
    return 1 if falhou or not itens else 0
