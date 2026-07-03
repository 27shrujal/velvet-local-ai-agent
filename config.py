"""Central configuration for the Velvet desktop AI agent."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DOCUMENTS_DIR = Path(os.getenv("DOCUMENTS_DIR", str(BASE_DIR / "documents")))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db")))
MANIFEST_PATH = CHROMA_DIR / "manifest.json"

MODEL_DISPLAY_NAME = os.getenv("MODEL_DISPLAY_NAME", "Velvet")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "velvet_documents")
TOP_K = int(os.getenv("TOP_K", "4"))

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Velvet")
USER_NAME = os.getenv("USER_NAME", "Shrujal")
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "en-in")
VOICE_RATE = int(os.getenv("VOICE_RATE", "175"))
VOICE_MAX_CHARS = int(os.getenv("VOICE_MAX_CHARS", "1200"))

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
