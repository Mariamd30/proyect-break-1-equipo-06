# Project Break 1 — RAG Engineering: Deporte Municipal

Asistente RAG sobre instalaciones, tarifas y normas del deporte municipal de Madrid.

## Instalación

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

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

## Preguntar

~~~bash
python main.py --query "¿Cuánto cuesta el abono de piscina?"
python main.py --ask "¿Cuánto cuesta el abono de piscina?"
~~~

## Streamlit

~~~bash
streamlit run app.py
~~~

## Fuentes del corpus

(completar con enlaces y fecha de descarga)
