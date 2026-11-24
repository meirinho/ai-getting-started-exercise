**Idiomas:** [English](README.md) · Português (Brasil) (este arquivo) · [Español](README.es.md)

# ia-como-comecar-exercicio

Código de exemplo da página «Como começar com IA» (degrau 1: local, CPU, sem GPU). Leva uma tarefa feita à mão — ler uma ata fictícia e responder três perguntas — a um fluxo que roda do começo ao fim e confere a saída contra um critério escrito antes de rodar.

```
PDF (pypdf) ─> chunks (fonte + página) ─> embeddings (sentence-transformers) ─> Chroma
                                                                      │
pergunta ─> busca ─> resposta (Ollama, ou extrativa no --modo-teste) ─┴─> saida/resultado.json
                                                                           │
                                                      python -m exercicio checar
                                                      python -m exercicio publicar  ─> docs/ (GitHub Pages, opcional)
```

## Do que precisa

- Linux, macOS ou Windows, com Python 3.11 ou mais novo (testado com Python 3.13 no Linux, CPU, sem GPU).
- Caminho padrão, local e gratuito: Python, Ollama, pypdf, sentence-transformers e Chroma.
- Opcionais: OpenRouter (LLM pela rede, com a sua chave numa variável de ambiente) e GitHub Pages (publicar a saída).
- Internet só para baixar o modelo de embeddings do Hugging Face, na primeira vez; depois o caminho local roda offline. O modo `--embeddings fake` não baixa modelo.
- Sem chave de API no caminho padrão. A chave da OpenRouter, se você usar essa opção, entra só em `OPENROUTER_API_KEY` (terminal ou arquivo `.env`, que o git ignora). Nunca no código.

Modelo de embeddings (baixado quando o código roda no modo `e5`, em `~/.cache/huggingface`):

| Papel | Modelo | Onde trocar |
|---|---|---|
| Embeddings | `intfloat/multilingual-e5-small` | `EXERCICIO_MODELO_EMBEDDINGS` |

## Instalação

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                           # PyTorch só de CPU
pytest -q
```

No caminho com Ollama, instale o [Ollama](https://ollama.com), inicie o serviço e baixe um modelo (`ollama pull llama3.2` é um exemplo; use o que já tiver na máquina).

## Como rodar

O critério de conclusão está em `CRITERIO.md` e em `criterio.yaml`, escritos **antes** do fluxo. A entrada é o PDF fictício `dados/ata-reuniao-ficticia.pdf`.

```bash
# documentos fictícios (já estão em dados/; o script recria o PDF)
python -m exercicio gerar-pdf

# modo de teste determinístico (sem Ollama e sem OpenRouter):
# resposta extrativa a partir dos trechos recuperados
python -m exercicio rodar --modo-teste --checar

# caminho padrão, com Ollama local (falha com mensagem clara se o Ollama não estiver no ar)
python -m exercicio rodar --llm ollama --modelo llama3.2 --checar

# opção pela OpenRouter (a chave vem só de OPENROUTER_API_KEY)
# Cole a sua chave no terminal, não num arquivo versionado.
export OPENROUTER_API_KEY=
python -m exercicio rodar --llm openrouter --modelo SEU_MODELO --checar

# conferência à parte, se a saída já existir
python -m exercicio checar

# passo opcional: gera docs/index.html a partir da saída, para o GitHub Pages
python -m exercicio publicar
```

O `--modo-teste` é o modo documentado para quando o Ollama não está instalado: a resposta é extrativa e determinística (copia o trecho mais parecido e cita arquivo e página; se o texto não trouxer a resposta, abstém-se). Os testes do pytest usam esse modo e embeddings `fake`, sem rede e sem download.

`--embeddings e5` (padrão) usa `intfloat/multilingual-e5-small`. `--embeddings fake` usa vetores determinísticos, só para teste ou para uma máquina sem o modelo em cache.

### Os sete passos do exercício

1. Escolher uma tarefa limitada e uma entrada sem informação sensível (aqui, a ata fictícia).
2. Escrever a saída esperada e o critério de conclusão **antes** de escolher ferramenta (`CRITERIO.md`).
3. Separar o que é regra (ler o PDF, cortar, gravar a saída, conferir) do que pede interpretação (a resposta em linguagem natural, quando há LLM).
4. Montar o caminho com a entrada local e ver o resultado no terminal (e, se quiser, em `docs/index.html`). Nada é enviado para fora no caminho padrão.
5. Rodar o caso conhecido e conferir contra o critério: `python -m exercicio checar`.
6. A pergunta fora do documento («Qual é a taxa de juros do financiamento imobiliário?») é o caso que deve falhar se o fluxo inventar a resposta; o certo é abster-se.
7. Decidir o próximo ajuste: outro modelo, o modo OpenRouter, ou publicar a saída no GitHub Pages.

### Configuração

Tudo por variável de ambiente (`exercicio/config.py`) ou flag:

- `EXERCICIO_LLM` — `ollama` (padrão), `openrouter` ou `teste` (o mesmo que `--llm` / `--modo-teste`).
- `EXERCICIO_LLM_MODELO` — nome no Ollama ou id na OpenRouter (`--modelo`).
- `OLLAMA_URL` — padrão `http://localhost:11434`.
- `OPENROUTER_API_KEY` — só no ambiente, nunca em arquivo versionado. O `.env.example` traz a variável vazia; copie para `.env` se quiser.
- `EXERCICIO_MODELO_EMBEDDINGS`, `EXERCICIO_EMBEDDINGS` (`e5` ou `fake`), `EXERCICIO_INDICE`, `EXERCICIO_SAIDA`.

### Publicar a saída no GitHub Pages (opcional)

1. Rode o fluxo e depois `python -m exercicio publicar`. Isso (re)escreve `docs/index.html`.
2. No GitHub, em Settings → Pages, escolha GitHub Actions como fonte.
3. Rode o workflow `Deploy GitHub Pages` à mão (Actions → o workflow → Run workflow). Ele está em `.github/workflows/pages.yml` e só dispara por `workflow_dispatch`: não publica nada em push nem em pull request.

## Testes

```bash
pytest -q
```

Os testes geram o PDF numa pasta temporária, rodam o fluxo com `--modo-teste` e embeddings `fake`, conferem o critério, simulam a OpenRouter com mock (sem rede) e checam se a chave não entra em arquivo. Não dependem do Ollama nem de download de modelo.

## Estrutura

```
exercicio/
  pdf.py             leitura do PDF com pypdf, texto por página
  chunks.py          corte com fonte e página, sem atravessar páginas
  embeddings.py      sentence-transformers (e5) ou vetores fake
  banco.py           Chroma persistido em disco
  responder.py       resposta extrativa, Ollama ou OpenRouter
  pipeline.py        fluxo de ponta a ponta
  checar.py          conferência contra criterio.yaml
  publicar.py        gera docs/index.html a partir da saída
  gerar_pdf.py       regenera o PDF fictício
  cli.py             python -m exercicio ...
CRITERIO.md          critério de conclusão, escrito antes de rodar
criterio.yaml        o mesmo critério, lido pela checagem
dados/               PDF fictício (CC BY 4.0)
docs/                HTML gerado para o GitHub Pages
indice/, saida/      índice do Chroma e saídas (fora do git)
.github/workflows/   pages.yml (só workflow_dispatch)
tests/               pytest
```

## Limites e erros comuns

- No caminho padrão, se o Ollama não estiver no ar, o fluxo termina com código 2 e uma mensagem pedindo o Ollama, o `--modo-teste` ou a OpenRouter. Não há tentativa silenciosa de outro backend.
- A resposta extrativa do `--modo-teste` só copia um trecho do documento: se o trecho certo não vier no topo da busca, a resposta erra mesmo com o trecho certo na lista.
- PDF com tabela ou duas colunas pode sair fora de ordem no pypdf; confira `saida/texto-extraido.txt` antes de confiar na resposta.
- Os chunks não atravessam páginas, para a citação continuar certa.
- A chave da OpenRouter nunca deve ir para o git. Se colar a chave num arquivo, use só o `.env` (ignorado). O `.env.example` permanece vazio.
- Fica de fora nesta versão: OCR, crawling, reranqueamento e tela interativa (isso está no repositório `ia-faca-voce-mesmo-rag`).

## Degraus

- Degrau 0: abrir a ata no leitor de PDF e copiar as respostas à mão, sem critério escrito.
- Degrau 1 (este repositório): um script local que lê o arquivo, responde e confere a saída.
- Degrau 2 (não incluído): agendamento, log no ar e comparação entre o caminho local e o caminho num servidor.

## Licença e atribuição

Código sob a licença MIT (`LICENSE`). O documento fictício de `dados/` sob CC BY 4.0 (`dados/LICENSE.md`). Os modelos baixados têm as licenças das suas páginas no Hugging Face.

## Limitações desta versão

- A integração com o Ollama e com a OpenRouter existe no código. Os testes cobrem o modo de teste e a OpenRouter com mock, sem rede. O Ollama precisa estar instalado e com um modelo baixado para o caminho padrão ser exercitado de ponta a ponta nesta máquina.
