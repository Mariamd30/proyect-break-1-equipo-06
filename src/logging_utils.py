"""Logging básico de cada consulta (pregunta, k, nº chunks, tiempo, modelo)."""

import json
import time
from pathlib import Path

RUTA_LOG = Path("output/retrieval_log.jsonl")


def log_query(pregunta: str, k: int, n_chunks: int, tiempo: float, modelo: str):
    """Registra la consulta en consola y en output/retrieval_log.jsonl."""
    entrada = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pregunta": pregunta,
        "k": k,
        "n_chunks": n_chunks,
        "tiempo_segundos": round(tiempo, 3),
        "modelo": modelo,
    }
    print(f"[log] k={k} chunks={n_chunks} tiempo={tiempo:.2f}s modelo={modelo} | \"{pregunta}\"")

    RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUTA_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")