from unittest.mock import patch

import pytest

from exercise.answer import LlmUnavailable, call_ollama, ollama_available
from exercise.store import SearchResult


def test_ollama_missing_clear_message():
    with patch("exercise.answer.requests.get", side_effect=ConnectionError("off")):
        assert ollama_available("http://localhost:11434") is False
    with patch("exercise.answer.ollama_available", return_value=False):
        with pytest.raises(LlmUnavailable, match="Ollama is not available"):
            call_ollama(
                "Quando é a próxima reunião?",
                [SearchResult("1", "text", "minutes.pdf", 1, 0.9)],
                "http://localhost:11434",
                "llama3.2",
            )


def test_ollama_without_model_clear_message():
    with pytest.raises(LlmUnavailable, match="EXERCISE_LLM_MODEL"):
        call_ollama("question", [], "http://localhost:11434", "")