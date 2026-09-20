# Project Break 1 — RAG Engineering: Deporte Municipal

Asistente RAG sobre instalaciones, tarifas y normas del deporte municipal de Madrid.

**Requiere API key:** solo para generar respuestas (`--ask` y Streamlit), con una
`GOOGLE_API_KEY` de Gemini. Indexar el corpus y `--query` funcionan sin clave.

Los embeddings se calculan en local con un modelo multilingüe (funciona bien en
español), sin cuota ni red una vez descargado el modelo (~470 MB, solo la primera vez).

**Resultado medido:** los mismos 1712 chunks que con Gemini no lograban
completarse en una sesión, con HF local se procesaron en **63 segundos**
(54 lotes de ~32 textos, ~1.18s/lote de media).

## Instalación

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

En Windows el entorno se activa con `.venv\Scripts\activate`. Edita `.env` y sustituye
`tu_api_key_aqui` por tu `GOOGLE_API_KEY` de Google AI Studio (solo hace falta para
`--ask` y Streamlit).

## 🔀 Embeddings: por qué usamos Hugging Face en vez de Gemini

El pipeline de embeddings usa **`sentence-transformers` (Hugging Face, local)**
en lugar de la API de Gemini. Aquí el porqué, por si alguien se pregunta al
ver el código.

### El problema

Con nuestro corpus (~1700 chunks tras el chunking), al generar los embeddings
con `gemini-embedding-001` topamos con el límite del **free tier** de Google:

- Primero saltó un `429 RESOURCE_EXHAUSTED` por límite de peticiones **por minuto**.
- Tras ajustar el tamaño de lote y añadir reintentos automáticos, seguía
  cortándose — el cuello de botella real era otro límite distinto: **RPD
  (Requests Per Day) = 1000 peticiones/día**.
- Cada texto embeddeado cuenta como una petición hacia ese contador diario,
  así que con ~1700 chunks necesitábamos casi el doble de lo que el free
  tier permite completar en un solo día.

### La alternativa

En vez de repartir la ingesta en 2 días (o pedir facturación de pago),
cambiamos a **embeddings locales**:

| | Valor |
|---|---|
| Librería | `sentence-transformers` |
| Modelo | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Dimensiones | 384 |
| Requiere API key | No — corre en tu máquina |

Es multilingüe (funciona bien en español) y no depende de cuota ni de red
una vez descargado el modelo (~470 MB, solo la primera vez).

### Instalación

```bash
pip install -r requirements.txt   # incluye sentence-transformers
```

### Importante si tocas `retriever.py` / `index.py`

- La pregunta del usuario debe embeddearse con **este mismo modelo**
  (`embed.embeddear_consulta(pregunta)`), no con Gemini — los espacios
  vectoriales de proveedores distintos no son compatibles entre sí.
- `embeddear_consulta()` **no recibe un `client`** (no hace falta
  autenticación para esto):
```python
  from embed import embeddear_consulta
  vector = embeddear_consulta("¿Cuánto cuesta el abono de piscina?")
```
- Si ves un `embeddings.json` con vectores de **3072** dimensiones (restos
  de una generación anterior con Gemini), bórralo y regenera con
  `ejecutar_embeddings()` — mezclar vectores de proveedores distintos en el
  mismo índice rompe el retrieval.

### Lo que NO cambia

La **generación** de la respuesta final sigue usando Gemini
(`GENERATION_MODEL`) — este cambio afecta solo a la fase de embeddings.

## Indexar el corpus

~~~bash
python main.py --index
~~~

Los directorios `chroma/` y `output/` no se suben al repositorio (están en `.gitignore`),
así que hay que indexar en local antes de preguntar. Si cambias el modelo de embeddings,
`CHUNK_SIZE` o `CHUNK_OVERLAP`, vuelve a ejecutar `--index` para regenerar el índice desde cero.

## Preguntar

Solo retrieval: muestra los fragmentos recuperados, sin usar Gemini.

~~~bash
python main.py --query "¿Cuánto cuesta el abono de piscina?"
python main.py --query "¿Cuánto cuesta el abono de piscina?" --k 5
~~~

RAG completo (retrieval + generación con Gemini): imprime la respuesta y las fuentes.
Si en los documentos no hay evidencia suficiente, el sistema se abstiene y lo indica.

~~~bash
python main.py --ask "¿Cuánto cuesta la entrada a la piscina de verano para adultos?"
python main.py --ask "¿Cuál es la capital de Francia?"
~~~

Cada consulta se registra en consola y en `output/retrieval_log.jsonl` (retrieval) y en
`output/generacion_log.jsonl` (pregunta, k, nº de chunks, tiempo, modelo, abstención y error).

## Configuración

Los parámetros están en `config.py`:

| Parámetro | Valor | Descripción |
|---|---|---|
| `TOP_K` | 3 | Fragmentos que recupera el retriever por defecto |
| `MAX_CHUNKS` | 5 | Máximo de fragmentos que se incluyen en el prompt; el slider de Streamlit llega hasta este valor |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 500 / 50 | Tamaño y solape del chunking |
| `GENERATION_MODEL` | `gemini-3.1-flash-lite` | Modelo de generación |
| `TEMPERATURE` | 0.0 | Temperatura de generación |

## Streamlit

~~~bash
streamlit run app.py
~~~

Chat sobre el corpus que llama a `responder()`. Muestra la respuesta con sus fuentes, un
desplegable con los fragmentos recuperados (fuente y score) y una tabla de métricas de la
sesión (pregunta, k, nº de fragmentos, tiempo, modelo y si hubo abstención).
El slider de la barra lateral cambia k. Requiere haber indexado antes (`--index`) y tener
`GOOGLE_API_KEY` en `.env`.

(Pendiente: añadir capturas de pantalla.)

## Evaluación

`queries/preguntas_eval.json` contiene 13 preguntas (10 dentro del corpus y 3 fuera) con la
fuente y la respuesta esperadas. Los criterios son: evidencia (la fuente esperada aparece entre
las fuentes devueltas), grounding (la respuesta se sostiene en el contexto y coincide con la
esperada, sin inventar) y abstención (solo debe abstenerse cuando `deberia_abstenerse` es true).

~~~bash
python main.py --eval           # evalúa las 13 preguntas con k por defecto (usa Gemini)
python main.py --eval --k 5     # igual, con otro valor de k
~~~

Para cada pregunta se imprime la respuesta, las fuentes, lo esperado y si el sistema se abstuvo;
la comparación se hace a mano. Resultados y análisis en `entregables/informe_decisiones.md`.

## Uso desde código (API interna)

~~~python
from src.logic import responder, rag_ask

resultado = responder("¿Cuánto cuesta la entrada a la piscina de verano para adultos?", k=3)
resultado["respuesta"]   # texto de la respuesta (o la frase de abstención)
resultado["abstencion"]  # True si el modelo se abstuvo
resultado["fuentes"]     # ficheros de los fragmentos recuperados
resultado["chunks"]      # fragmentos con texto, fuente y score
resultado["error"]       # mensaje de error o None (responder no lanza excepciones)

rag_ask("¿Cuál es el horario de taquilla de un centro?")  # solo texto, pensada como tool de un agente
~~~

## Fuentes del corpus

(completar con enlaces y fecha de descarga)
