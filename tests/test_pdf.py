from exercise.pdf import read_pdf


def test_pdf_has_anchor_phrases(pdf_sample):
    pages = read_pdf(pdf_sample)
    assert pages
    text = "\n".join(p.text for p in pages)
    assert "15 de dezembro de 2026" in text
    assert "4.800,00" in text
    assert "Carla Dias" in text
    assert pages[0].method == "pypdf"
    assert pages[0].page == 1
    assert pages[0].source == pdf_sample.name


def test_missing_pdf_reports_path(tmp_path):
    from exercise.pdf import read_pdf
    import pytest

    missing = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError, match="missing"):
        read_pdf(missing)