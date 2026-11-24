"""Conferência estática do Dockerfile e do docker-compose.yml (sem o Docker)."""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]


def test_dockerignore_exclui_env():
    texto = (RAIZ / ".dockerignore").read_text(encoding="utf-8")
    assert ".env\n" in texto or texto.strip().endswith(".env")
    assert any(ln.strip() == ".env" for ln in texto.splitlines())


def test_env_example_continua_vazio():
    for linha in (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines():
        if linha.startswith("OPENROUTER_API_KEY="):
            assert linha.strip() == "OPENROUTER_API_KEY="


def test_dockerfile_instala_requirements_e_roda_o_exercicio():
    texto = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
    froms = [ln for ln in texto.splitlines() if ln.startswith("FROM ")]
    assert froms and froms[0].startswith("FROM python:") and "slim" in froms[0]
    assert "pip install" in texto and "requirements.txt" in texto
    assert '"python", "-m", "exercicio"' in texto or "python -m exercicio" in texto
    assert "OPENROUTER_API_KEY=" not in texto or "OPENROUTER_API_KEY=\n" in texto


def test_compose_sobe_ollama_saudavel_e_aponta_o_exercicio():
    dados = yaml.safe_load((RAIZ / "docker-compose.yml").read_text(encoding="utf-8"))
    servicos = dados["services"]
    assert "ollama" in servicos and "exercicio" in servicos
    ollama = servicos["ollama"]
    assert "healthcheck" in ollama
    assert any("ollama" in str(v) for v in ollama["volumes"])
    dep = servicos["exercicio"]["depends_on"]
    assert dep["ollama"]["condition"] == "service_healthy"
    env = servicos["exercicio"]["environment"]
    assert env["OLLAMA_URL"] == "http://ollama:11434"
    # A chave, se existir, só entra por interpolação do ambiente; aqui o valor é vazio.
    chave = str(env.get("OPENROUTER_API_KEY", ""))
    assert chave in ("", "${OPENROUTER_API_KEY:-}")
    volumes = servicos["exercicio"]["volumes"]
    assert any("huggingface" in v or "hf-cache" in v for v in volumes)


def test_compose_tem_passo_para_baixar_o_modelo():
    dados = yaml.safe_load((RAIZ / "docker-compose.yml").read_text(encoding="utf-8"))
    init = dados["services"]["ollama-init"]
    assert init["depends_on"]["ollama"]["condition"] == "service_healthy"
    comando = " ".join(str(x) for x in ([init.get("entrypoint")] + [init.get("command")]))
    assert "pull" in comando
    assert "qwen2.5:0.5b" in str(init.get("command"))


def test_arquivos_docker_nao_trazem_chave():
    for nome in ("Dockerfile", "docker-compose.yml", ".dockerignore", ".env.example"):
        texto = (RAIZ / nome).read_text(encoding="utf-8")
        for linha in texto.splitlines():
            m = linha.strip()
            if m.startswith("OPENROUTER_API_KEY="):
                assert m == "OPENROUTER_API_KEY=" or m.endswith(":-}") or m.endswith(":-}")
            assert "sk-" not in linha
