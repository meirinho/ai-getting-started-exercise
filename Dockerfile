# Imagem do exercício: Python slim, dependências do requirements.txt.
# O Ollama fica num serviço à parte (veja docker-compose.yml).
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ANONYMIZED_TELEMETRY=False \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/root/.cache/huggingface \
    EXERCICIO_LLM=ollama

WORKDIR /app

# libgomp: usado pelo onnxruntime (dependência do Chroma) nesta imagem slim.
# A versão acompanha o repositório da imagem slim; não fixamos o pacote aqui.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Padrão: rodar o fluxo com o Ollama do compose e conferir o critério.
# Sobrescreva o comando para --modo-teste, pytest, checar ou publicar.
CMD ["python", "-m", "exercicio", "rodar", "--llm", "ollama", "--checar"]
