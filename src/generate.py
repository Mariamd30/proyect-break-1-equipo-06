"""Generación RAG: prompt + LLM, con abstención si no hay evidencia."""


def responder(pregunta: str) -> dict:
    raise NotImplementedError


def rag_ask(consulta: str) -> str:
    return responder(consulta)["respuesta"]
