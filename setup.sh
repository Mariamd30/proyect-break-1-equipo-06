#!/bin/bash
set -e

mkdir -p src data queries entregables

cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.pyc
.env
chroma/
output/
.DS_Store
EOF

cat > .env.example << 'EOF'
GOOGLE_API_KEY=tu_api_key_aqui
EOF

cat > requirements.txt << 'EOF'
langchain
langchain-google-genai
chromadb
streamlit
python-dotenv
EOF

cat > config.py << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Modelos ---
EMBEDDING_MODEL = "models/embedding-001"
GENERATION_MODEL = "gemini-1.5-flash"
TEMPERATURE = 0.0

# --- Chunking ---
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# --- Retrieval ---
TOP_K = 3
MAX_CHUNKS = 5

# --- Paths ---
DATA_DIR = "data"
CHROMA_DIR = "chroma"
EOF

cat > main.py << 'EOF'
import argparse


def main():
    parser = argparse.ArgumentParser(description="RAG CLI - Deporte municipal")
    parser.add_argument("--index", action="store_true", help="Indexar el corpus")
    parser.add_argument("--query", type=str, help="Solo retrieval: mostrar chunks recuperados")
    parser.add_argument("--ask", type=str, help="Pregunta RAG completa (retrieval + generación)")
    parser.add_argument("--k", type=int, default=None, help="Override de TOP_K")

    args = parser.parse_args()

    if args.index:
        print("TODO: indexar corpus")
    elif args.query:
        print(f"TODO: retrieval para: {args.query}")
    elif args.ask:
        print(f"TODO: RAG completo para: {args.ask}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
EOF

cat > app.py << 'EOF'
import streamlit as st

st.set_page_config(page_title="RAG Deporte Municipal", page_icon="🏊")
st.title("Asistente de Deporte Municipal")

st.write("Skeleton en construcción")
EOF

touch src/__init__.py

cat > src/load.py << 'EOF'
"""Carga de documentos del corpus (data/) en memoria."""


def load_documents(data_dir: str) -> list:
    raise NotImplementedError
EOF

cat > src/chunk.py << 'EOF'
"""Chunking de documentos cargados."""


def chunk_documents(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    raise NotImplementedError
EOF

cat > src/embed.py << 'EOF'
"""Generación de embeddings para los chunks."""


def embed_chunks(chunks: list) -> list:
    raise NotImplementedError
EOF

cat > src/index.py << 'EOF'
"""Construcción y gestión del índice ChromaDB persistente."""


def build_index(chunks: list, embeddings: list, persist_dir: str):
    raise NotImplementedError
EOF

cat > src/retrieve.py << 'EOF'
"""Retrieval: dada una pregunta, recupera los top-k chunks más relevantes."""


def retrieve(query: str, k: int) -> list:
    raise NotImplementedError
EOF

cat > src/generate.py << 'EOF'
"""Generación RAG: prompt + LLM, con abstención si no hay evidencia."""


def responder(pregunta: str) -> dict:
    raise NotImplementedError


def rag_ask(consulta: str) -> str:
    return responder(consulta)["respuesta"]
EOF

cat > src/logging_utils.py << 'EOF'
"""Logging básico de cada consulta."""


def log_query(pregunta: str, k: int, n_chunks: int, tiempo: float, modelo: str):
    raise NotImplementedError
EOF

touch data/.gitkeep
touch queries/.gitkeep

cat > entregables/informe_decisiones.md << 'EOF'
# Informe de decisiones — Project Break 1: RAG Engineering

## 1. Tema y corpus
- Tema: Deporte municipal
- Fuentes: (completar)
- Formatos: CSV/XLSX + PDF

## 2. Experimento de chunking
- CHUNK_SIZE / CHUNK_OVERLAP probados:
- Observaciones:

## 3. Retrieval — observación con 2 valores de K
- K=3 vs K=5:
- Observaciones:

## 4. Generación
- 1 acierto in-corpus:
- 1 abstención fuera de corpus:

## 5. Fallos conocidos (3) y próximos pasos
1.
2.
3.
EOF

cat > README.md << 'EOF'
# Project Break 1 — RAG Engineering: Deporte Municipal

Asistente RAG sobre instalaciones, tarifas y normas del deporte municipal de Madrid.

## Instalación

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

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
EOF

echo "Estructura creada correctamente."