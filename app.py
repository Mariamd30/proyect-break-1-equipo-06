"""Interfaz Streamlit del asistente RAG de deporte municipal.

La lógica vive en src.logic.responder(); aquí solo se pinta el chat.

  streamlit run app.py   (requiere el índice: python main.py --index)
"""

from pathlib import Path

import streamlit as st

from config import MAX_CHUNKS, TOP_K
from src.logic import responder

BIENVENIDA = (
    "Hola, soy el asistente del deporte municipal de Madrid. "
    "Pregúntame por tarifas, instalaciones, horarios o normas de uso."
)


def mensaje_bienvenida() -> dict:
    return {"role": "assistant", "content": BIENVENIDA, "fuentes": [], "chunks": [], "error": False}


def render_mensaje(message: dict) -> None:
    """Pinta el contenido de un mensaje (se llama dentro de un st.chat_message)."""
    if message["error"]:
        st.error(message["content"])
    else:
        st.markdown(message["content"])

    if message["fuentes"]:
        st.caption("Fuentes: " + ", ".join(f"`{f}`" for f in message["fuentes"]))

    if message["chunks"]:
        with st.expander(f"Fragmentos recuperados ({len(message['chunks'])})"):
            for i, chunk in enumerate(message["chunks"], 1):
                st.markdown(f"**{i}. `{Path(chunk['source']).name}`** · score {chunk['score']:.3f}")
                st.text(chunk["text"])


st.set_page_config(page_title="RAG Deporte Municipal", page_icon="🏊")

st.title("Asistente de Deporte Municipal")
st.caption("RAG sobre instalaciones, tarifas y normas del deporte municipal de Madrid")

if "messages" not in st.session_state:
    st.session_state.messages = [mensaje_bienvenida()]
    st.session_state.metricas = []

with st.sidebar:
    st.header("Configuración")
    k = st.slider("Top-K (fragmentos)", min_value=1, max_value=MAX_CHUNKS, value=TOP_K)
    st.caption("Índice: `chroma/` (ejecuta `python main.py --index`).")
    if st.button("Limpiar chat", width="stretch"):
        st.session_state.messages = [mensaje_bienvenida()]
        st.session_state.metricas = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_mensaje(message)

if pregunta := st.chat_input("Tu pregunta sobre deporte municipal..."):
    usuario = {"role": "user", "content": pregunta, "fuentes": [], "chunks": [], "error": False}
    st.session_state.messages.append(usuario)
    with st.chat_message("user"):
        render_mensaje(usuario)

    with st.chat_message("assistant"):
        with st.status("Consultando el corpus...", expanded=False) as status:
            resultado = responder(pregunta, k=k)
            status.update(label="Listo", state="complete")

        # Las fuentes solo se muestran si el modelo respondió (no en abstención ni en error)
        fuentes = resultado["fuentes"]
        if resultado["abstencion"] or resultado["error"]:
            fuentes = []

        if resultado["error"]:
            texto = resultado["error"]
        else:
            texto = resultado["respuesta"]
            # Una fila de la tabla de métricas por cada pregunta respondida
            st.session_state.metricas.append({
                "Pregunta": pregunta[:60],
                "k": resultado["k"],
                "Fragmentos": resultado["n_chunks"],
                "Tiempo (s)": round(resultado["tiempo_segundos"], 1),
                "Modelo": resultado["modelo"],
                "Abstención": "sí" if resultado["abstencion"] else "no",
            })

        respuesta = {
            "role": "assistant",
            "content": texto,
            "fuentes": fuentes,
            "chunks": resultado["chunks"],
            "error": bool(resultado["error"]),
        }
        render_mensaje(respuesta)

    st.session_state.messages.append(respuesta)

if st.session_state.metricas:
    with st.expander("Métricas de la sesión"):
        st.dataframe(st.session_state.metricas, hide_index=True, width="stretch")
