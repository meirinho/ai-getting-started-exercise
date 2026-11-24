"""Resposta a partir dos trechos recuperados: modo teste, Ollama ou OpenRouter."""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field

import requests

from .banco import Resultado
from .config import ABSTENCAO

STOP = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "no", "na", "nas", "nos",
    "e", "ou", "que", "qual", "quais", "quando", "quem", "como",
    "para", "por", "com", "pelo", "pela", "pelos", "pelas",
    "ao", "à", "aos", "às", "é", "foi", "será", "ser",
    "the", "of", "and", "is", "a", "an",
}


@dataclass
class Resposta:
    texto: str
    citacoes: list[str] = field(default_factory=list)
    absteve: bool = False
    modo: str = "teste"
    modelo: str = "extrativo-local"

    def como_dict(self) -> dict:
        return asdict(self)


def _tokens(texto: str) -> set[str]:
    return {t for t in re.findall(r"\w+", texto.lower(), flags=re.UNICODE) if t not in STOP and len(t) > 2}


def _sobreposicao(pergunta: str, trecho: str) -> float:
    q, t = _tokens(pergunta), _tokens(trecho)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)




def extrativa(pergunta: str, resultados: list[Resultado], limiar: float, modo_embeddings: str) -> Resposta:
    if not resultados:
        return Resposta(ABSTENCAO, [], True, "teste", "extrativo-local")
    topo = resultados[0]
    # Abstenção no modo extrativo: pouca sobreposição de tokens de conteúdo
    # com qualquer trecho. O e5 costuma dar cosseno alto até em pergunta
    # fora do documento; o cosseno sozinho não decide a abstenção.
    overlap = max(_sobreposicao(pergunta, r.texto) for r in resultados)
    if overlap < 0.25:
        return Resposta(ABSTENCAO, [], True, "teste", "extrativo-local")
    # O trecho do topo inteiro: o PDF pode quebrar a linha no meio de um
    # valor (por exemplo "R$\n4.800,00"), e cortar por linha perderia o número.
    trecho = " ".join(topo.texto.split())
    return Resposta(
        f"«{trecho}» [{topo.citacao()}]",
        [topo.citacao()],
        False,
        "teste",
        "extrativo-local",
    )


def ollama_disponivel(url: str, timeout: float = 2.0) -> bool:
    try:
        r = requests.get(url.rstrip("/") + "/api/tags", timeout=timeout)
        return r.ok
    except (requests.RequestException, OSError):
        return False


class LlmIndisponivel(RuntimeError):
    """O backend de LLM pedido não está disponível."""


def _mensagem_ollama_ausente(url: str) -> str:
    return (
        f"Ollama não está disponível em {url}. "
        "Instale e inicie o Ollama, ou rode com --modo-teste "
        "(resposta extrativa determinística, sem LLM), "
        "ou configure OPENROUTER_API_KEY e use --llm openrouter."
    )


def _mensagem_openrouter_sem_chave() -> str:
    return (
        "O modo OpenRouter pede a variável de ambiente OPENROUTER_API_KEY "
        "(defina no terminal ou num arquivo .env, que o git ignora; "
        "nunca coloque a chave no código). "
        "Sem chave, use --modo-teste ou --llm ollama."
    )


def _prompt(pergunta: str, resultados: list[Resultado]) -> list[dict]:
    contexto = "\n\n".join(f"[{r.citacao()}]\n{r.texto}" for r in resultados)
    sistema = (
        "Responda em português do Brasil usando SOMENTE os trechos dados. "
        "Cite o arquivo e a página no formato [arquivo, p. N]. "
        f"Se os trechos não trouxerem a resposta, responda exatamente: {ABSTENCAO}"
    )
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": f"Trechos:\n{contexto}\n\nPergunta: {pergunta}"},
    ]


def _texto_e_abstencao(texto: str, resultados: list[Resultado]) -> Resposta:
    texto = (texto or "").strip()
    absteve = (not texto) or (ABSTENCAO.lower() in texto.lower())
    if absteve:
        return Resposta(ABSTENCAO if not texto else texto, [], True)
    citacoes = [r.citacao() for r in resultados[:1]]
    # Se o modelo já citou no texto, aproveita; senão acrescenta a do topo.
    if resultados and resultados[0].citacao() not in texto:
        texto = f"{texto} [{resultados[0].citacao()}]"
    return Resposta(texto, citacoes, False)


def chamar_ollama(pergunta: str, resultados: list[Resultado], url: str, modelo: str) -> Resposta:
    if not modelo:
        raise LlmIndisponivel(
            "O modo Ollama pede EXERCICIO_LLM_MODELO (o nome de um modelo "
            "já baixado no Ollama, por exemplo llama3.2)."
        )
    if not ollama_disponivel(url):
        raise LlmIndisponivel(_mensagem_ollama_ausente(url))
    r = requests.post(
        url.rstrip("/") + "/api/chat",
        json={"model": modelo, "messages": _prompt(pergunta, resultados), "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    dados = r.json()
    texto = (dados.get("message") or {}).get("content") or ""
    resp = _texto_e_abstencao(texto, resultados)
    resp.modo = "ollama"
    resp.modelo = modelo
    return resp


def chamar_openrouter(pergunta: str, resultados: list[Resultado], modelo: str) -> Resposta:
    chave = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not chave:
        raise LlmIndisponivel(_mensagem_openrouter_sem_chave())
    if not modelo:
        raise LlmIndisponivel(
            "O modo OpenRouter pede EXERCICIO_LLM_MODELO "
            "(o id do modelo na OpenRouter)."
        )
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {chave}"},
        json={"model": modelo, "messages": _prompt(pergunta, resultados)},
        timeout=120,
    )
    r.raise_for_status()
    dados = r.json()
    escolha = (dados.get("choices") or [{}])[0]
    texto = ((escolha.get("message") or {}).get("content")) or ""
    resp = _texto_e_abstencao(texto, resultados)
    resp.modo = "openrouter"
    resp.modelo = modelo
    return resp


def responder(
    pergunta: str,
    resultados: list[Resultado],
    cfg,
) -> Resposta:
    if cfg.llm == "teste":
        return extrativa(pergunta, resultados, cfg.limiar_similaridade, cfg.embeddings)
    if cfg.llm == "ollama":
        return chamar_ollama(pergunta, resultados, cfg.ollama_url, cfg.llm_modelo)
    if cfg.llm == "openrouter":
        return chamar_openrouter(pergunta, resultados, cfg.llm_modelo)
    raise LlmIndisponivel(f"LLM desconhecido: {cfg.llm}")


def garantir_backend(cfg) -> None:
    """Falhar cedo, antes de indexar, se o LLM pedido não puder ser usado."""
    if cfg.llm == "teste":
        return
    if cfg.llm == "ollama":
        if not cfg.llm_modelo:
            raise LlmIndisponivel(
                "O modo Ollama pede EXERCICIO_LLM_MODELO (o nome de um modelo "
                "já baixado no Ollama, por exemplo llama3.2)."
            )
        if not ollama_disponivel(cfg.ollama_url):
            raise LlmIndisponivel(_mensagem_ollama_ausente(cfg.ollama_url))
        return
    if cfg.llm == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise LlmIndisponivel(_mensagem_openrouter_sem_chave())
        if not cfg.llm_modelo:
            raise LlmIndisponivel(
                "O modo OpenRouter pede EXERCICIO_LLM_MODELO "
                "(o id do modelo na OpenRouter)."
            )
        return
    raise LlmIndisponivel(f"LLM desconhecido: {cfg.llm}")
