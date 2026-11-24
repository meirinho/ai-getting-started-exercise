import numpy as np

from exercicio.embeddings import embed_pergunta, embed_trechos


def test_fake_e_deterministico_e_normalizado():
    a = embed_trechos("fake", ["Carla Dias entrega o relatório de novembro."])
    b = embed_trechos("fake", ["Carla Dias entrega o relatório de novembro."])
    assert a.shape[1] == 128
    assert np.allclose(a, b)
    assert np.isclose(np.linalg.norm(a[0]), 1.0, atol=1e-5)


def test_fake_aproxima_textos_parecidos():
    trechos = [
        "A próxima reunião será no dia 15 de dezembro de 2026, às 14h.",
        "O valor aprovado foi de R$ 4.800,00 para material de escritório.",
    ]
    vetores = embed_trechos("fake", trechos)
    q = embed_pergunta("fake", "Quando é a próxima reunião?")
    sims = vetores @ q
    assert sims[0] > sims[1]
