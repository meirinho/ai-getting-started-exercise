# Exercise image: Python slim + requirements.txt. Ollama runs as a sidecar (see docker-compose.yml).
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ANONYMIZED_TELEMETRY=False \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/root/.cache/huggingface \
    EXERCISE_LLM=ollama

WORKDIR /app

# libgomp: onnxruntime (Chroma dependency) on slim images.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the flow against Compose Ollama and check criteria.
# Override for --test-mode, pytest, check, or publish.
CMD ["python", "-m", "exercise", "run", "--llm", "ollama", "--check"]