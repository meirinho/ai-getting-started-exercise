import os
from unittest.mock import patch

import pytest

from exercicio.banco import Resultado
from exercicio.config import Config
from exercicio.responder import LlmIndisponivel, chamar_openrouter, responder


def _cfg():
    cfg = Config()
    cfg.llm = "openrouter"
    cfg.llm_modelo = "modelo-de-teste"
    return cfg


def _trechos():
    return [
        Resultado("1", "A próxima reunião será no dia 15 de dezembro de 2026.", "ata.pdf", 1, 0.9)
    ]


def test_openrouter_sem_chave_falha_sem_rede():
    os.environ.pop("OPENROUTER_API_KEY", None)
    with pytest.raises(LlmIndisponivel, match="OPENROUTER_API_KEY"):
        chamar_openrouter("Quando é a próxima reunião?", _trechos(), "modelo-de-teste")


def test_openrouter_usa_a_chave_do_ambiente_e_nao_abre_rede():
    os.environ["OPENROUTER_API_KEY"] = "chave-de-teste-nao-usar"
    corpo = {
        "choices": [
            {
                "message": {
                    "content": "A próxima reunião é em 15 de dezembro de 2026. [ata.pdf, p. 1]"
                }
            }
        ]
    }
    with patch("exercicio.responder.requests.post") as post:
        post.return_value.json.return_value = corpo
        post.return_value.raise_for_status.return_value = None
        resp = responder("Quando é a próxima reunião?", _trechos(), _cfg())
    os.environ.pop("OPENROUTER_API_KEY", None)
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer chave-de-teste-nao-usar"
    assert kwargs["json"]["model"] == "modelo-de-teste"
    assert resp.modo == "openrouter"
    assert "15 de dezembro de 2026" in resp.texto
    assert not resp.absteve


def test_chave_de_teste_nao_entra_em_arquivo(tmp_path, cfg):
    os.environ["OPENROUTER_API_KEY"] = "chave-de-teste-nao-usar"
    from exercicio import pipeline

    cfg.llm = "teste"  # o fluxo dos testes não chama a API
    pipeline.rodar(cfg)
    texto = (cfg.pasta_saida / "resultado.json").read_text(encoding="utf-8")
    os.environ.pop("OPENROUTER_API_KEY", None)
    assert "chave-de-teste-nao-usar" not in texto
    assert "OPENROUTER_API_KEY=" not in texto
