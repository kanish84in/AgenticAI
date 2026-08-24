import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

# =====================================================
# General Reasoning Model
#
# Used for:
# - intent/planning
# - reflection
# - other reasoning tasks
# =====================================================

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:4b"
)


# =====================================================
# SQL Generation Model
#
# Dedicated code-focused model.
#
# This avoids the long thinking behaviour that we saw
# with qwen3:4b during SQL generation.
# =====================================================

OLLAMA_SQL_MODEL = os.getenv(
    "OLLAMA_SQL_MODEL",
    "qwen2.5-coder:3b"
)

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://localhost:11434"
)

SQLITE_DB_PATH = PROJECT_ROOT / os.getenv(
    "SQLITE_DB_PATH",
    "data/chinook.db"
)

FALKORDB_HOST = os.getenv(
    "FALKORDB_HOST",
    "localhost"
)


FALKORDB_PORT = int(
    os.getenv(
        "FALKORDB_PORT",
        "6379"
    )
)


FALKORDB_GRAPH = os.getenv(
    "FALKORDB_GRAPH",
    "text2sql_semantic"
)


EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "embeddinggemma"
)

VECTOR_TOP_K = int(
    os.getenv(
        "VECTOR_TOP_K",
        "3"
    )
)

VECTOR_MIN_SCORE = float(
    os.getenv(
        "VECTOR_MIN_SCORE",
        "0.50"
    )
)