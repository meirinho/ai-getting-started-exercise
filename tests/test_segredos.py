import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
IGNORAR_PARTES = {".venv", "__pycache__", ".git", ".pytest_cache", "indice", "saida"}


def _iter_arquivos():
    for p in RAIZ.rglob("*"):
        if not p.is_file():
            continue
        if any(parte in IGNORAR_PARTES for parte in p.parts):
            continue
        yield p


def test_env_example_tem_chave_vazia():
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    assert "OPENROUTER_API_KEY=" in texto
    for linha in texto.splitlines():
        if linha.startswith("OPENROUTER_API_KEY="):
            assert linha.strip() == "OPENROUTER_API_KEY="


def test_nenhum_arquivo_versionavel_tem_chave():
    for p in _iter_arquivos():
        try:
            texto = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for linha in texto.splitlines():
            m = re.match(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*)$", linha)
            if not m or linha.strip().startswith("#"):
                continue
            valor = m.group(1).split("#", 1)[0].strip().strip("'").strip('"')
            # Atribuição real da variável: o valor precisa ser vazio.
            assert valor == "", f"valor em {p}: {linha!r}"
