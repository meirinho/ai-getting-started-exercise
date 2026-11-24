from exercicio.pdf import ler_pdf


def test_pdf_tem_frases_ancora(pdf_exemplo):
    paginas = ler_pdf(pdf_exemplo)
    assert paginas
    texto = "\n".join(p.texto for p in paginas)
    assert "15 de dezembro de 2026" in texto
    assert "4.800,00" in texto
    assert "Carla Dias" in texto
    assert paginas[0].metodo == "pypdf"
    assert paginas[0].pagina == 1
    assert paginas[0].fonte == pdf_exemplo.name


def test_pdf_ausente_fala_o_caminho(tmp_path):
    from exercicio.pdf import ler_pdf
    import pytest

    faltando = tmp_path / "nao-existe.pdf"
    with pytest.raises(FileNotFoundError, match="nao-existe"):
        ler_pdf(faltando)
