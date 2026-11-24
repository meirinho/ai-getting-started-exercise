"""Static checks for Dockerfile and docker-compose.yml (no Docker daemon)."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_dockerignore_excludes_env():
    text = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert ".env\n" in text or text.strip().endswith(".env")
    assert any(line.strip() == ".env" for line in text.splitlines())


def test_env_example_stays_empty():
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            assert line.strip() == "OPENROUTER_API_KEY="


def test_dockerfile_installs_requirements_and_runs_exercise():
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    froms = [line for line in text.splitlines() if line.startswith("FROM ")]
    assert froms and froms[0].startswith("FROM python:") and "slim" in froms[0]
    assert "pip install" in text and "requirements.txt" in text
    assert '"python", "-m", "exercise"' in text or "python -m exercise" in text
    assert "OPENROUTER_API_KEY=" not in text or "OPENROUTER_API_KEY=\n" in text


def test_compose_starts_healthy_ollama_and_wires_exercise():
    data = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = data["services"]
    assert "ollama" in services and "exercise" in services
    ollama = services["ollama"]
    assert "healthcheck" in ollama
    assert any("ollama" in str(v) for v in ollama["volumes"])
    dep = services["exercise"]["depends_on"]
    assert dep["ollama"]["condition"] == "service_healthy"
    env = services["exercise"]["environment"]
    assert env["OLLAMA_URL"] == "http://ollama:11434"
    key = str(env.get("OPENROUTER_API_KEY", ""))
    assert key in ("", "${OPENROUTER_API_KEY:-}")
    volumes = services["exercise"]["volumes"]
    assert any("huggingface" in v or "hf-cache" in v for v in volumes)


def test_compose_pulls_default_model():
    data = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    init = data["services"]["ollama-init"]
    assert init["depends_on"]["ollama"]["condition"] == "service_healthy"
    command = " ".join(str(x) for x in ([init.get("entrypoint")] + [init.get("command")]))
    assert "pull" in command
    assert "qwen2.5:1.5b" in str(init.get("command"))
    exercise = data["services"]["exercise"]["environment"]
    assert "qwen2.5:1.5b" in str(exercise.get("EXERCISE_LLM_MODEL"))


def test_docker_files_do_not_contain_api_keys():
    for name in ("Dockerfile", "docker-compose.yml", ".dockerignore", ".env.example"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("OPENROUTER_API_KEY="):
                assert stripped == "OPENROUTER_API_KEY=" or stripped.endswith(":-}") or stripped.endswith(":-}")
            assert "sk-" not in line


def test_workflow_docker_e2e_has_no_secrets():
    path = ROOT / ".github" / "workflows" / "docker-e2e.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    triggers = data.get("on") or data.get(True) or {}
    assert "pull_request" in triggers
    assert "workflow_dispatch" in triggers
    assert data.get("permissions", {}).get("contents") == "read"
    job = data["jobs"]["e2e"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["timeout-minutes"] == 30
    assert "secrets" not in job
    env = job.get("env") or {}
    assert "OPENROUTER_API_KEY" not in env
    assert "EXERCISE_LLM_MODEL" not in env
    text = path.read_text(encoding="utf-8")
    assert "secrets." not in text
    assert "OPENROUTER_API_KEY" not in text
    assert "EXERCISE_LLM_MODEL" not in text
    steps = job["steps"]
    uses = [step.get("uses") for step in steps if "uses" in step]
    assert uses == ["actions/checkout@v4"]
    if_map = {step["name"]: step.get("if") for step in steps}
    assert if_map.get("Compose logs on failure") == "failure()"
    assert if_map.get("Tear down") == "always()"
    script = "\n".join(step.get("run") or "" for step in steps)
    assert "docker compose up -d --build" in script
    assert "docker compose wait ollama-init" in script
    assert "docker compose run --rm exercise" in script
    assert "python -m exercise check" in script
    assert "6 items checked, 6 ok, 0 failed." in script
    assert "docker compose down -v" in script
    assert "docker compose logs" in script