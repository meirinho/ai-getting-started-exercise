"""Generate the fictional sample PDF at data/fictional-meeting-minutes.pdf."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from .config import Config

TITLE = "ATA DE REUNIÃO — Oficina Fictícia Meirinho"

PARAGRAPHS = [
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


def _font_with_accents():
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            pdfmetrics.registerFont(TTFont("ExerciseSans", str(candidate)))
            return "ExerciseSans"
    return "Helvetica"


def _wrap(c, text: str, font: str, size: int, width: float) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if c.stringWidth(trial, font, size) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def generate(path: Path | None = None) -> Path:
    cfg = Config.from_env()
    dest = path or (cfg.root_dir / "data" / "fictional-meeting-minutes.pdf")
    dest.parent.mkdir(parents=True, exist_ok=True)
    font = _font_with_accents()
    canvas_obj = canvas.Canvas(str(dest), pagesize=A4)
    canvas_obj.setTitle(TITLE)
    canvas_obj.setAuthor("Adriano Meirinho")
    width, height = A4
    margin = 2.2 * cm
    y = height - margin
    text_width = width - 2 * margin

    for i, paragraph in enumerate(PARAGRAPHS):
        size = 13 if i == 0 else 11
        canvas_obj.setFont(font, size)
        for line in _wrap(canvas_obj, paragraph, font, size, text_width):
            if y < margin + 2 * cm:
                canvas_obj.showPage()
                y = height - margin
                canvas_obj.setFont(font, size)
            canvas_obj.drawString(margin, y, line)
            y -= 16 if i == 0 else 15
        y -= 10 if i == 0 else 8

    canvas_obj.showPage()
    canvas_obj.save()
    return dest