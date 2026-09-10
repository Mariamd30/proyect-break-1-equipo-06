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
