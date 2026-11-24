from exercise.chunks import split_pages
from exercise.pdf import Page


def test_chunks_do_not_cross_pages():
    pages = [
        Page("a.pdf", 1, "First paragraph on page one.\n\nSecond paragraph still on page one."),
        Page("a.pdf", 2, "Text only on page two, with more than a few words."),
    ]
    chunks = split_pages(pages, size=80, overlap=10)
    assert chunks
    for chunk in chunks:
        assert chunk.source == "a.pdf"
        assert chunk.page in (1, 2)
        if chunk.page == 1:
            assert "page two" not in chunk.text
        else:
            assert "page one" not in chunk.text


def test_short_page_becomes_one_chunk():
    pages = [Page("a.pdf", 1, "One sentence only.")]
    chunks = split_pages(pages, size=400, overlap=60)
    assert len(chunks) == 1
    assert chunks[0].text == "One sentence only."