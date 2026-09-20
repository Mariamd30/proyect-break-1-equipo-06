"""Interfaz Streamlit del asistente RAG de deporte municipal.

La lógica vive en src.logic.responder(); aquí solo se pinta el chat.

  streamlit run app.py   (requiere el índice: python main.py --index)
"""

import streamlit as st

from config import MAX_CHUNKS, TOP_K
from src.logic import responder

BIENVENIDA = (
    "Hola, soy el asistente del deporte municipal de Madrid. "
    "Pregúntame por tarifas, instalaciones, horarios o normas de uso."
)


def mensaje_bienvenida() -> dict:
    return {"role": "assistant", "content": BIENVENIDA, "fuentes": [], "error": False}


def render_mensaje(message: dict) -> None:
    """Pinta el contenido de un mensaje (se llama dentro de un st.chat_message)."""
    if message["error"]:
        st.error(message["content"])
    else:
        st.markdown(message["content"])

    if message["fuentes"]:
        st.caption("Fuentes: " + ", ".join(f"`{f}`" for f in message["fuentes"]))


st.set_page_config(page_title="RAG Deporte Municipal", page_icon="🏊")

with st.sidebar:
    st.header("Configuración")
    k = st.slider("Top-K (fragmentos)", min_value=1, max_value=MAX_CHUNKS, value=TOP_K)
    st.caption("Índice: `chroma/` (ejecuta `python main.py --index`).")
    if st.button("Limpiar chat", width="stretch"):
        st.session_state.messages = [mensaje_bienvenida()]
        st.rerun()

st.title("Asistente de Deporte Municipal")
st.caption("RAG sobre instalaciones, tarifas y normas del deporte municipal de Madrid")

if "messages" not in st.session_state:
    st.session_state.messages = [mensaje_bienvenida()]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_mensaje(message)

if pregunta := st.chat_input("Tu pregunta sobre deporte municipal..."):
    usuario = {"role": "user", "content": pregunta, "fuentes": [], "error": False}
    st.session_state.messages.append(usuario)
    with st.chat_message("user"):
        render_mensaje(usuario)

    with st.chat_message("assistant"):
        with st.status("Consultando el corpus...", expanded=False) as status:
            resultado = responder(pregunta, k=k)
            status.update(label="Listo", state="complete")

        respuesta = {
            "role": "assistant",
            "content": resultado["error"] or resultado["respuesta"],
            "fuentes": [] if resultado["abstencion"] or resultado["error"] else resultado["fuentes"],
            "error": bool(resultado["error"]),
        }
        render_mensaje(respuesta)

    st.session_state.messages.append(respuesta)
