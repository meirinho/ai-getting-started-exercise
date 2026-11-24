from exercise.answer import extractive
from exercise.config import ABSTENTION_MESSAGE
from exercise.store import SearchResult


def test_off_topic_abstains_despite_high_cosine():
    hits = [
        SearchResult(
            "1",
            "A próxima reunião será no dia 15 de dezembro de 2026, às 14h.",
            "minutes.pdf",
            1,
            0.92,
        )
    ]
    answer = extractive(
        "Qual é a taxa de juros do financiamento imobiliário?",
        hits,
        threshold=0.35,
        embedding_mode="e5",
    )
    assert answer.abstained
    assert ABSTENTION_MESSAGE in answer.text


def test_known_question_does_not_abstain():
    hits = [
        SearchResult(
            "1",
            "A próxima reunião será no dia 15 de dezembro de 2026, às 14h.",
            "minutes.pdf",
            1,
            0.7,
        )
    ]
    answer = extractive("Quando é a próxima reunião?", hits, 0.35, "e5")
    assert not answer.abstained
    assert "15 de dezembro de 2026" in answer.text
    assert "minutes.pdf, p. 1" in answer.citations[0]


def test_budget_with_low_cosine_does_not_abstain():
    hits = [
        SearchResult(
            "1",
            "Ficou aprovado o valor de R$ 4.800,00 para material de escritório.",
            "minutes.pdf",
            1,
            0.20,
        )
    ]
    answer = extractive("Qual foi o orçamento aprovado?", hits, 0.35, "fake")
    assert not answer.abstained
    assert "4.800,00" in answer.text