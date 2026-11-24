from exercicio.banco import Resultado
from exercicio.config import ABSTENCAO
from exercicio.responder import extrativa


def test_pergunta_fora_abstém_mesmo_com_cosseno_alto():
    trechos = [
        Resultado(
            "1",
            "A próxima reunião será no dia 15 de dezembro de 2026, às 14h.",
            "ata.pdf",
            1,
            0.92,
        )
    ]
    resp = extrativa(
        "Qual é a taxa de juros do financiamento imobiliário?",
        trechos,
        limiar=0.35,
        modo_embeddings="e5",
    )
    assert resp.absteve
    assert ABSTENCAO in resp.texto


def test_pergunta_conhecida_nao_abstém():
    trechos = [
        Resultado(
            "1",
            "A próxima reunião será no dia 15 de dezembro de 2026, às 14h.",
            "ata.pdf",
            1,
            0.7,
        )
    ]
    resp = extrativa("Quando é a próxima reunião?", trechos, 0.35, "e5")
    assert not resp.absteve
    assert "15 de dezembro de 2026" in resp.texto
    assert "ata.pdf, p. 1" in resp.citacoes[0]


def test_orçamento_com_cosseno_baixo_nao_abstém():
    trechos = [
        Resultado(
            "1",
            "Ficou aprovado o valor de R$ 4.800,00 para material de escritório.",
            "ata.pdf",
            1,
            0.20,
        )
    ]
    resp = extrativa("Qual foi o orçamento aprovado?", trechos, 0.35, "fake")
    assert not resp.absteve
    assert "4.800,00" in resp.texto
