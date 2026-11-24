from unittest.mock import patch

import pytest

from exercicio.banco import Resultado
from exercicio.responder import LlmIndisponivel, chamar_ollama, ollama_disponivel


def test_ollama_ausente_mensagem_clara():
    with patch("exercicio.responder.requests.get", side_effect=ConnectionError("off")):
        assert ollama_disponivel("http://localhost:11434") is False
    with patch("exercicio.responder.ollama_disponivel", return_value=False):
        with pytest.raises(LlmIndisponivel, match="Ollama não está disponível"):
            chamar_ollama(
                "Quando é a próxima reunião?",
                [Resultado("1", "texto", "ata.pdf", 1, 0.9)],
                "http://localhost:11434",
                "llama3.2",
            )


def test_ollama_sem_modelo_mensagem_clara():
    with pytest.raises(LlmIndisponivel, match="EXERCICIO_LLM_MODELO"):
        chamar_ollama("pergunta", [], "http://localhost:11434", "")
