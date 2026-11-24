from exercicio.chunks import cortar
from exercicio.pdf import Pagina


def test_chunks_nao_atravessam_paginas():
    paginas = [
        Pagina("a.pdf", 1, "Primeiro parágrafo da página um.\n\nSegundo parágrafo ainda na página um."),
        Pagina("a.pdf", 2, "Texto exclusivo da página dois, com mais de algumas palavras."),
    ]
    pedacos = cortar(paginas, tamanho=80, sobreposicao=10)
    assert pedacos
    for c in pedacos:
        assert c.fonte == "a.pdf"
        assert c.pagina in (1, 2)
        if c.pagina == 1:
            assert "página dois" not in c.texto
        else:
            assert "página um" not in c.texto


def test_pagina_curta_vira_um_chunk():
    paginas = [Pagina("a.pdf", 1, "Uma frase só.")]
    pedacos = cortar(paginas, tamanho=400, sobreposicao=60)
    assert len(pedacos) == 1
    assert pedacos[0].texto == "Uma frase só."
