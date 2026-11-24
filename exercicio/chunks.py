"""Corte do texto em chunks, sem atravessar páginas, com fonte e página."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass

from .pdf import Pagina


@dataclass
class Chunk:
    id: str
    fonte: str
    pagina: int
    texto: str
    inicio: int
    fim: int

    def metadados(self) -> dict:
        d = asdict(self)
        d.pop("texto")
        d.pop("id")
        return d


def _id(fonte: str, pagina: int, inicio: int) -> str:
    return hashlib.sha1(f"{fonte}|{pagina}|{inicio}".encode()).hexdigest()[:16]


def _ajustar_fim(texto: str, inicio: int, fim: int) -> int:
    if fim >= len(texto):
        return len(texto)
    espaco = texto.rfind(" ", inicio + 1, fim)
    return espaco if espaco > inicio + (fim - inicio) // 2 else fim


def _faixas_fixas(texto: str, tamanho: int, sobreposicao: int) -> list[tuple[int, int]]:
    if tamanho <= 0:
        raise ValueError("tamanho precisa ser maior que zero")
    if not 0 <= sobreposicao < tamanho:
        raise ValueError("sobreposição precisa ficar entre 0 e tamanho - 1")
    if not texto.strip():
        return []
    if len(texto) <= tamanho:
        return [(0, len(texto))]
    faixas, inicio = [], 0
    while inicio < len(texto):
        fim = _ajustar_fim(texto, inicio, inicio + tamanho)
        faixas.append((inicio, fim))
        if fim >= len(texto):
            break
        inicio = max(fim - sobreposicao, inicio + 1)
    return faixas


def _faixas_paragrafo(texto: str, tamanho: int, sobreposicao: int) -> list[tuple[int, int]]:
    """Junta parágrafos até o tamanho. Um parágrafo longo cai no corte fixo."""
    paragrafos = list(re.finditer(r"\S(?:.|\n)*?(?:\n[ \t]*\n|$)", texto))
    if not paragrafos:
        return _faixas_fixas(texto, tamanho, sobreposicao)
    faixas: list[tuple[int, int]] = []
    acc_ini: int | None = None
    acc_fim: int | None = None

    def despejar_longo(ini: int, fim: int) -> None:
        for a, b in _faixas_fixas(texto[ini:fim], tamanho, sobreposicao):
            faixas.append((ini + a, ini + b))

    for m in paragrafos:
        ini, fim = m.start(), m.end()
        if acc_ini is None:
            if (fim - ini) > tamanho:
                despejar_longo(ini, fim)
                acc_ini, acc_fim = None, None
            else:
                acc_ini, acc_fim = ini, fim
            continue
        if (fim - acc_ini) <= tamanho:
            acc_fim = fim
            continue
        faixas.append((acc_ini, acc_fim))
        if (fim - ini) > tamanho:
            despejar_longo(ini, fim)
            acc_ini, acc_fim = None, None
        else:
            acc_ini, acc_fim = ini, fim
    if acc_ini is not None and acc_fim is not None:
        faixas.append((acc_ini, acc_fim))
    return faixas


def cortar(paginas: list[Pagina], tamanho: int = 400, sobreposicao: int = 60) -> list[Chunk]:
    chunks: list[Chunk] = []
    for pagina in paginas:
        if not pagina.texto.strip():
            continue
        for inicio, fim in _faixas_paragrafo(pagina.texto, tamanho, sobreposicao):
            trecho = pagina.texto[inicio:fim].strip()
            if not trecho:
                continue
            chunks.append(
                Chunk(
                    id=_id(pagina.fonte, pagina.pagina, inicio),
                    fonte=pagina.fonte,
                    pagina=pagina.pagina,
                    texto=trecho,
                    inicio=inicio,
                    fim=fim,
                )
            )
    return chunks
