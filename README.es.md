**Idiomas:** [English](README.md) · [Português (Brasil)](README.pt-BR.md) · Español (este archivo)

# ia-como-comecar-exercicio

Código de ejemplo de la página «Como começar com IA» (peldaño 1: local, CPU, sin GPU). Convierte una tarea hecha a mano —leer un acta ficticia y responder tres preguntas— en un flujo que corre de principio a fin y contrasta la salida con un criterio escrito antes de ejecutarlo.

```
PDF (pypdf) ─> chunks (fuente + página) ─> embeddings (sentence-transformers) ─> Chroma
                                                                      │
pregunta ─> búsqueda ─> respuesta (Ollama, o extractiva con --modo-teste) ─┴─> saida/resultado.json
                                                                               │
                                                          python -m exercicio checar
                                                          python -m exercicio publicar  ─> docs/ (GitHub Pages, opcional)
```

## Qué necesitas

- Linux, macOS o Windows, con Python 3.11 o más nuevo (probado con Python 3.13 en Linux, CPU, sin GPU).
- Camino predeterminado, local y gratuito: Python, Ollama, pypdf, sentence-transformers y Chroma.
- Opcionales: OpenRouter (un LLM por la red, con tu clave en una variable de entorno), GitHub Pages (para publicar la salida) y Docker Compose (para levantar Ollama y el ejercicio juntos).
- Internet solo para descargar el modelo de embeddings de Hugging Face, la primera vez; después el camino local corre sin red. `--embeddings fake` no descarga ningún modelo.
- Sin clave de API en el camino predeterminado. Si usas OpenRouter, la clave entra solo en `OPENROUTER_API_KEY` (el terminal o un archivo `.env`, que git ignora). Nunca en el código.

Modelo de embeddings (se descarga cuando corres el código en modo `e5`, en `~/.cache/huggingface`):

| Papel | Modelo | Dónde cambiarlo |
|---|---|---|
| Embeddings | `intfloat/multilingual-e5-small` | `EXERCICIO_MODELO_EMBEDDINGS` |

## Instalación

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt                           # PyTorch solo de CPU
pytest -q
```

En el camino con Ollama, instala [Ollama](https://ollama.com), arranca el servicio y descarga un modelo (`ollama pull llama3.2` es un ejemplo; usa el que ya tengas en la máquina).

## Cómo ejecutarlo

El criterio de conclusión está en `CRITERIO.md` y en `criterio.yaml`, escritos **antes** del flujo. La entrada es el PDF ficticio `dados/ata-reuniao-ficticia.pdf`.

```bash
# documento ficticio (ya está en dados/; el script recrea el PDF)
python -m exercicio gerar-pdf

# modo de prueba determinista (sin Ollama y sin OpenRouter):
# respuesta extractiva a partir de los pasajes recuperados
python -m exercicio rodar --modo-teste --checar

# camino predeterminado, con Ollama local (falla con un mensaje claro si Ollama no está en marcha)
python -m exercicio rodar --llm ollama --modelo llama3.2 --checar

# opción por OpenRouter (la clave sale solo de OPENROUTER_API_KEY)
# Pega tu clave en el terminal, no en un archivo versionado.
export OPENROUTER_API_KEY=
python -m exercicio rodar --llm openrouter --modelo TU_MODELO --checar

# comprobación aparte, si la salida ya existe
python -m exercicio checar

# paso opcional: genera docs/index.html a partir de la salida, para GitHub Pages
python -m exercicio publicar
```

`--modo-teste` es el modo documentado cuando Ollama no está instalado: la respuesta es extractiva y determinista (copia el pasaje más parecido y cita el archivo y la página; si el texto no trae la respuesta, se abstiene). Las pruebas de pytest usan este modo y embeddings `fake`, sin red y sin descarga.

`--embeddings e5` (el predeterminado) usa `intfloat/multilingual-e5-small`. `--embeddings fake` usa vectores deterministas, para las pruebas o para una máquina sin el modelo en caché.

### Los siete pasos del ejercicio

1. Elegir una tarea limitada y una entrada sin información sensible (aquí, el acta ficticia).
2. Escribir la salida esperada y el criterio de conclusión **antes** de elegir herramienta (`CRITERIO.md`).
3. Separar lo que es regla (leer el PDF, cortar, guardar la salida, comprobarla) de lo que pide interpretación (la respuesta en lenguaje natural, cuando hay un LLM).
4. Armar el camino con la entrada local y ver el resultado en el terminal (y, si quieres, en `docs/index.html`). El camino predeterminado no envía nada fuera de la máquina.
5. Ejecutar el caso conocido y comprobarlo contra el criterio: `python -m exercicio checar`.
6. La pregunta fuera del documento («Qual é a taxa de juros do financiamento imobiliário?») es el caso que debería fallar si el flujo inventa la respuesta; lo correcto es abstenerse.
7. Decidir el siguiente ajuste: otro modelo, el modo OpenRouter, o publicar la salida en GitHub Pages.

### Configuración

Todo va por variable de entorno (`exercicio/config.py`) o por flag:

- `EXERCICIO_LLM` — `ollama` (predeterminado), `openrouter` o `teste` (lo mismo que `--llm` / `--modo-teste`).
- `EXERCICIO_LLM_MODELO` — el nombre en Ollama o el id en OpenRouter (`--modelo`).
- `OLLAMA_URL` — predeterminado `http://localhost:11434`.
- `OPENROUTER_API_KEY` — solo en el entorno, nunca en un archivo versionado. `.env.example` trae la variable vacía; cópiala a `.env` si quieres.
- `EXERCICIO_MODELO_EMBEDDINGS`, `EXERCICIO_EMBEDDINGS` (`e5` o `fake`), `EXERCICIO_INDICE`, `EXERCICIO_SAIDA`.

### Publicar la salida en GitHub Pages (opcional)

1. Ejecuta el flujo y después `python -m exercicio publicar`. Esto (re)escribe `docs/index.html`.
2. En GitHub, en Settings → Pages, elige GitHub Actions como fuente.
3. Ejecuta el workflow `Deploy GitHub Pages` a mano (Actions → el workflow → Run workflow). Está en `.github/workflows/pages.yml` y solo se dispara por `workflow_dispatch`: no publica nada en un push ni en un pull request.


## Con Docker

El camino sin Docker, en las secciones de arriba, sigue valiendo. Con Docker Compose (v2), `docker compose up --build` levanta Ollama, descarga un modelo pequeño y corre el flujo, comprobando la salida contra el criterio.

```bash
docker compose up --build
# la primera vez: descarga las imágenes, el modelo qwen2.5:0.5b (se cambia con EXERCICIO_LLM_MODELO)
# y el modelo de embeddings, en el volumen hf-cache
# la salida aparece en saida/ en el equipo
```

Para descargar el modelo a mano, o usar otro (por ejemplo `llama3.2:1b`):

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull qwen2.5:0.5b
docker compose run --rm --no-deps exercicio python -m exercicio rodar --llm ollama --modelo qwen2.5:0.5b --checar
```

Sin LLM (modo de prueba), sin levantar Ollama:

```bash
docker compose run --rm --no-deps exercicio python -m exercicio rodar --modo-teste --checar
docker compose run --rm --no-deps exercicio pytest -q
```

La clave de OpenRouter, si usas esa opción, entra solo en `OPENROUTER_API_KEY` en el entorno o en un `.env` local (git lo ignora; el `.dockerignore` también lo deja fuera de la imagen). `.env.example` se queda vacío. No pongas la clave en `docker-compose.yml`.

## Pruebas

```bash
pytest -q
```

Las pruebas generan el PDF en una carpeta temporal, corren el flujo con `--modo-teste` y embeddings `fake`, comprueban el criterio, simulan OpenRouter con un mock (sin red) y verifican que la clave no entre en ningún archivo. No dependen de Ollama ni de la descarga de un modelo.

## Estructura

```
exercicio/
  pdf.py             lectura del PDF con pypdf, texto por página
  chunks.py          corte con fuente y página, sin cruzar páginas
  embeddings.py      sentence-transformers (e5) o vectores fake
  banco.py           Chroma persistido en disco
  responder.py       respuesta extractiva, Ollama o OpenRouter
  pipeline.py        flujo de principio a fin
  checar.py          comprobación contra criterio.yaml
  publicar.py        genera docs/index.html a partir de la salida
  gerar_pdf.py       regenera el PDF ficticio
  cli.py             python -m exercicio ...
CRITERIO.md          criterio de conclusión, escrito antes de ejecutar
criterio.yaml        el mismo criterio, leído por la comprobación
dados/               PDF ficticio (CC BY 4.0)
docs/                HTML generado para GitHub Pages
indice/, saida/      índice de Chroma y salidas (fuera de git)
.github/workflows/   pages.yml (solo workflow_dispatch)
Dockerfile           imagen Python slim del ejercicio
docker-compose.yml   Ollama, la descarga del modelo y el ejercicio
.dockerignore        excluye .env, .venv, el índice y la salida
tests/               pytest
```

## Límites y errores comunes

- En el camino predeterminado, si Ollama no está en marcha, el flujo termina con el código 2 y un mensaje que pide Ollama, `--modo-teste` o OpenRouter. No cambia de backend en silencio.
- La respuesta extractiva de `--modo-teste` solo copia un pasaje del documento: si el pasaje correcto no queda arriba en la búsqueda, la respuesta falla aunque ese pasaje esté en la lista.
- Un PDF con tabla o dos columnas puede salir desordenado en pypdf; revisa `saida/texto-extraido.txt` antes de confiar en la respuesta.
- Los chunks no cruzan páginas, para que la cita siga siendo correcta.
- La clave de OpenRouter nunca debe ir al git. Si pegas la clave en un archivo, usa solo `.env` (ignorado). `.env.example` se queda vacío.
- Queda fuera de esta versión: OCR, crawling, reranking y una pantalla interactiva (eso está en el repositorio `ia-faca-voce-mesmo-rag`).
- La primera ejecución con Docker descarga las imágenes, el modelo de Ollama y, en el modo `e5`, el modelo de embeddings; hace falta red y espacio en disco.

## Peldaños

- Peldaño 0: abrir el acta en el lector de PDF y copiar las respuestas a mano, sin un criterio escrito.
- Peldaño 1 (este repositorio): un script local que lee el archivo, responde y comprueba la salida.
- Peldaño 2 (no incluido): programación, un registro en la red y la comparación entre el camino local y el camino en un servidor.

## Licencia y atribución

Código bajo la licencia MIT (`LICENSE`). El documento ficticio de `dados/` bajo CC BY 4.0 (`dados/LICENSE.md`). Los modelos descargados tienen las licencias de sus páginas en Hugging Face.

## Limitaciones de esta versión

- La integración con Ollama y con OpenRouter existe en el código. Las pruebas cubren el modo de prueba y OpenRouter con un mock, sin red. Ollama tiene que estar instalado y con un modelo descargado para que el camino predeterminado se ejercite de principio a fin en esta máquina.
