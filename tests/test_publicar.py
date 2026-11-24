from exercicio import pipeline, publicar


def test_publicar_gera_html_com_as_respostas(cfg):
    pipeline.rodar(cfg)
    caminho = publicar.publicar(cfg)
    assert caminho.is_file()
    html = caminho.read_text(encoding="utf-8")
    assert "15 de dezembro de 2026" in html
    assert "4.800,00" in html
    assert "Carla Dias" in html
    assert "<html" in html
    assert "sk-" not in html
