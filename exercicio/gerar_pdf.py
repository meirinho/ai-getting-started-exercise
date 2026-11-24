"""Gera o PDF fictício de exemplo em dados/ata-reuniao-ficticia.pdf."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .config import Config

TITULO = "ATA DE REUNIÃO — Oficina Fictícia Meirinho"

PARAGRAFOS = [
    "ATA DE REUNIÃO — Oficina Fictícia Meirinho",
    "Data: 10 de novembro de 2026",
    "Local: Sala 3, Cidade Fictícia",
    "Presentes: Ana Souza (coordenação), Bruno Lima (financeiro) e Carla Dias (operação).",
    (
        "Pauta e deliberações. Orçamento do trimestre: ficou aprovado o valor de "
        "R$ 4.800,00 para material de escritório no trimestre de janeiro a março de 2027."
    ),
    (
        "Relatório mensal: a responsável pelo relatório de novembro é Carla Dias, "
        "com entrega até 5 de dezembro de 2026."
    ),
    (
        "Próxima reunião: a próxima reunião será no dia 15 de dezembro de 2026, "
        "às 14h, na mesma sala."
    ),
    (
        "Esta ata é um documento fictício, criado só para o exercício. "
        "Não descreve reunião, empresa nem pessoa reais."
    ),
]


def _fonte_com_acento():
    """Tenta uma fonte TrueType do sistema; se não houver, usa Helvetica."""
    candidatas = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    ]
    for c in candidatas:
        if c.is_file():
            pdfmetrics.registerFont(TTFont("ExercicioSans", str(c)))
            return "ExercicioSans"
    return "Helvetica"


def _quebrar(c, texto: str, fonte: str, tamanho: int, largura: float) -> list[str]:
    palavras = texto.split()
    linhas, atual = [], ""
    for palavra in palavras:
        tentativa = palavra if not atual else f"{atual} {palavra}"
        if c.stringWidth(tentativa, fonte, tamanho) <= largura:
            atual = tentativa
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas or [texto]


def gerar(caminho: Path | None = None) -> Path:
    cfg = Config.do_ambiente()
    destino = caminho or (cfg.pasta_raiz / "dados" / "ata-reuniao-ficticia.pdf")
    destino.parent.mkdir(parents=True, exist_ok=True)
    fonte = _fonte_com_acento()
    c = canvas.Canvas(str(destino), pagesize=A4)
    c.setTitle(TITULO)
    c.setAuthor("Adriano Meirinho")
    largura, altura = A4
    margem = 2.2 * cm
    y = altura - margem
    largura_texto = largura - 2 * margem

    for i, paragrafo in enumerate(PARAGRAFOS):
        tamanho = 13 if i == 0 else 11
        c.setFont(fonte, tamanho)
        for linha in _quebrar(c, paragrafo, fonte, tamanho, largura_texto):
            if y < margem + 2 * cm:
                c.showPage()
                y = altura - margem
                c.setFont(fonte, tamanho)
            c.drawString(margem, y, linha)
            y -= 16 if i == 0 else 15
        y -= 10 if i == 0 else 8

    c.showPage()
    c.save()
    return destino
