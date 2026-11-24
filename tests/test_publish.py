from exercise import pipeline, publish


def test_publish_writes_html_with_answers(cfg):
    pipeline.run(cfg)
    path = publish.publish(cfg)
    assert path.is_file()
    html = path.read_text(encoding="utf-8")
    assert "15 de dezembro de 2026" in html
    assert "4.800,00" in html
    assert "Carla Dias" in html
    assert "<html" in html
    assert "sk-" not in html