import os
from unittest.mock import patch

import pytest

from exercise.answer import LlmUnavailable, answer_question, call_openrouter
from exercise.config import Config
from exercise.store import SearchResult


def _cfg():
    cfg = Config()
    cfg.llm = "openrouter"
    cfg.llm_model = "test-model"
    return cfg


def _hits():
    return [
        SearchResult("1", "A próxima reunião será no dia 15 de dezembro de 2026.", "minutes.pdf", 1, 0.9)
    ]


def test_openrouter_without_key_fails_without_network():
    os.environ.pop("OPENROUTER_API_KEY", None)
    with pytest.raises(LlmUnavailable, match="OPENROUTER_API_KEY"):
        call_openrouter("Quando é a próxima reunião?", _hits(), "test-model")


def test_openrouter_uses_env_key_without_network():
    os.environ["OPENROUTER_API_KEY"] = "test-key-not-for-production"
    body = {
        "choices": [
            {
                "message": {
                    "content": "A próxima reunião é em 15 de dezembro de 2026. [minutes.pdf, p. 1]"
                }
            }
        ]
    }
    with patch("exercise.answer.requests.post") as post:
        post.return_value.json.return_value = body
        post.return_value.raise_for_status.return_value = None
        answer = answer_question("Quando é a próxima reunião?", _hits(), _cfg())
    os.environ.pop("OPENROUTER_API_KEY", None)
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer test-key-not-for-production"
    assert kwargs["json"]["model"] == "test-model"
    assert answer.mode == "openrouter"
    assert "15 de dezembro de 2026" in answer.text
    assert not answer.abstained


def test_test_key_not_written_to_output(tmp_path, cfg):
    os.environ["OPENROUTER_API_KEY"] = "test-key-not-for-production"
    from exercise import pipeline

    cfg.llm = "test"
    pipeline.run(cfg)
    text = (cfg.output_dir / "result.json").read_text(encoding="utf-8")
    os.environ.pop("OPENROUTER_API_KEY", None)
    assert "test-key-not-for-production" not in text
    assert "OPENROUTER_API_KEY=" not in text