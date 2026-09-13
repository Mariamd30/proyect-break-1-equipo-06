"""Generación de embeddings con Gemini.

Toma los chunks generados por chunk.py, los convierte en vectores numéricos
con Gemini y guarda dos artefactos que consumirá index/retrieval:

  output/chunks.json      -> chunks con texto + metadata (sin vector)
  output/embeddings.json  -> texto + vector + metadata (lo que se indexa)

Requiere GOOGLE_API_KEY en .env (ver config.py).

IMPORTANTE (free tier): el proceso guarda el progreso en embeddings.json
después de CADA lote. Si se corta por un 429 de cuota (por minuto o por
día), puedes volver a ejecutar ejecutar_embeddings() más tarde y retomará
justo donde se quedó, sin repetir chunks ya embebidos.
"""

import json
import re
import time
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from langchain_core.documents import Document

from config import (
    CHUNKS_JSON,
    EMBED_BATCH_SIZE,
    EMBEDDING_MODEL,
    EMBEDDINGS_JSON,
    GOOGLE_API_KEY,
)


def _extraer_vector(embedding_obj) -> list[float]:
    """La API devuelve objetos con .values; esto unifica el formato a list[float]."""
    if hasattr(embedding_obj, "values"):
        return list(embedding_obj.values)
    return list(embedding_obj)


def documentos_a_dicts(documentos: list[Document]) -> list[dict]:
    """Convierte Document de LangChain a dict serializable en JSON."""
    return [
        {"text": doc.page_content, "metadata": dict(doc.metadata)}
        for doc in documentos
    ]


def guardar_chunks_json(chunks: list[Document], ruta: str | Path) -> Path:
    """Escribe chunks.json (texto + metadata, sin vector) para depuración."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_chunks": len(chunks),
        "chunks": documentos_a_dicts(chunks),
    }
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def _segundos_de_espera(mensaje: str, por_defecto: float = 20.0) -> float:
    """Extrae 'retry in ~Ns' del mensaje de error 429, si viene incluido."""
    m = re.search(r"retry in (\d+(?:\.\d+)?)s", mensaje)
    return float(m.group(1)) + 2 if m else por_defecto


def _embed_con_reintento(client: genai.Client, contents, intentos: int = 3):
    """Llama a embed_content reintentando ante 429 (cuota). Pocos intentos
    porque si la cuota es diaria, reintentar en bucle no sirve de nada:
    mejor guardar lo hecho y que el usuario reintente más tarde."""
    for intento in range(1, intentos + 1):
        try:
            return client.models.embed_content(model=EMBEDDING_MODEL, contents=contents)
        except genai_errors.ClientError as exc:
            es_429 = "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc)
            if not es_429 or intento == intentos:
                raise
            espera = _segundos_de_espera(str(exc))
            print(f"  [429] cuota agotada, reintento {intento}/{intentos} en {espera:.0f}s...")
            time.sleep(espera)


def embeddear_textos(client: genai.Client, textos: list[str]) -> list[list[float]]:
    """Envía una lista corta de textos a Gemini en una sola llamada.

    Pensada para textos sueltos (p. ej. una pregunta de usuario), no para
    el corpus completo -- para eso usa ejecutar_embeddings(), que persiste
    progreso lote a lote.
    """
    if not textos:
        return []

    contents = [types.Content(parts=[types.Part(text=t)]) for t in textos]
    result = _embed_con_reintento(client, contents)
    vectores = [_extraer_vector(emb) for emb in result.embeddings]
    if len(vectores) != len(textos):
        raise RuntimeError(
            f"La API devolvió {len(vectores)} vectores para {len(textos)} "
            f"textos — revisa EMBEDDING_MODEL en config.py."
        )
    return vectores


def embeddear_consulta(client: genai.Client, pregunta: str) -> list[float]:
    """Un vector para la pregunta (mismo modelo que el índice). Lo usará
    Persona 2 en su retriever para mantener el mismo espacio de embeddings.
    """
    return embeddear_textos(client, [pregunta])[0]


# ---------------------------------------------------------------------------
# Ingesta completa del corpus, con progreso reanudable
# ---------------------------------------------------------------------------


def _cargar_progreso(ruta: str | Path) -> list[dict]:
    """Lee embeddings.json si ya existe de una ejecución anterior (parcial
    o completa) y devuelve los items ya embebidos."""
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data.get("items", [])


def _guardar_progreso(ruta: str | Path, items: list[dict], total_esperado: int) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "embedding_model": EMBEDDING_MODEL,
        "total": len(items),
        "total_esperado": total_esperado,
        "completo": len(items) >= total_esperado,
        "dimensions": len(items[0]["vector"]) if items else 0,
        "items": items,
    }
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def ejecutar_embeddings(chunks: list[Document]) -> tuple[list[dict], Path]:
    """Orquesta: chunks -> chunks.json -> vectores -> embeddings.json.

    Reanudable: si embeddings.json ya tiene N items de una ejecución
    anterior (misma lista de chunks, mismo orden), continúa desde el
    chunk N en vez de volver a embeddear todo desde cero.
    """
    guardar_chunks_json(chunks, CHUNKS_JSON)

    items = _cargar_progreso(EMBEDDINGS_JSON)
    ya_hechos = len(items)
    if ya_hechos:
        print(f"Reanudando: {ya_hechos}/{len(chunks)} chunks ya embebidos previamente.")

    pendientes = chunks[ya_hechos:]
    if not pendientes:
        print("Nada que hacer: el corpus ya estaba completamente embebido.")
        return items, Path(EMBEDDINGS_JSON)

    client = genai.Client(api_key=GOOGLE_API_KEY)
    inicio_tiempo = time.perf_counter()

    for inicio in range(0, len(pendientes), EMBED_BATCH_SIZE):
        lote = pendientes[inicio : inicio + EMBED_BATCH_SIZE]
        textos = [c.page_content for c in lote]

        try:
            vectores = embeddear_textos(client, textos)
        except genai_errors.ClientError:
            print(
                f"  Cuota agotada tras {ya_hechos + inicio}/{len(chunks)} chunks. "
                f"Progreso guardado en {EMBEDDINGS_JSON} — vuelve a ejecutar más "
                f"tarde para continuar desde aquí."
            )
            raise

        for chunk, vector in zip(lote, vectores):
            items.append(
                {"text": chunk.page_content, "vector": vector, "metadata": dict(chunk.metadata)}
            )

        _guardar_progreso(EMBEDDINGS_JSON, items, len(chunks))
        print(f"  {ya_hechos + inicio + len(lote)}/{len(chunks)} embebidos y guardados")

    latencia_ms = (time.perf_counter() - inicio_tiempo) * 1000
    print(f"Embeddings completos: {len(pendientes)} chunks nuevos en {latencia_ms:.0f} ms ({EMBEDDING_MODEL})")

    ruta = Path(EMBEDDINGS_JSON)
    print(f"  Guardado final: {ruta} ({items[0]['vector'].__len__() if items else 0} dimensiones)")
    return items, ruta
