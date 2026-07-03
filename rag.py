"""Local document indexing and retrieval for Retrieval-Augmented Generation."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    DOCUMENTS_DIR,
    EMBEDDING_MODEL,
    MANIFEST_PATH,
    OLLAMA_BASE_URL,
    TOP_K,
)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


class KnowledgeBase:
    def __init__(self) -> None:
        self.embeddings = OllamaEmbeddings(
            model=EMBEDDING_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
        self.vector_store: Chroma | None = None

    @staticmethod
    def _document_files() -> list[Path]:
        return sorted(
            path
            for path in DOCUMENTS_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    @staticmethod
    def _fingerprint(files: Iterable[Path]) -> str:
        digest = hashlib.sha256()
        for path in files:
            stat = path.stat()
            digest.update(str(path.relative_to(DOCUMENTS_DIR)).encode("utf-8"))
            digest.update(str(stat.st_size).encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def _load_file(path: Path) -> list[Document]:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            loader = TextLoader(str(path), encoding="utf-8", autodetect_encoding=True)
        elif suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        elif suffix == ".docx":
            loader = Docx2txtLoader(str(path))
        else:
            return []

        documents = loader.load()
        for document in documents:
            document.metadata["source"] = str(path.relative_to(DOCUMENTS_DIR))
        return documents

    def _create_store(self) -> Chroma:
        return Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DIR),
        )

    def _read_manifest(self) -> dict:
        if not MANIFEST_PATH.exists():
            return {}
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def index_documents(self, force: bool = False) -> str:
        files = self._document_files()
        if not files:
            self.vector_store = self._create_store()
            return (
                f"No supported documents were found in {DOCUMENTS_DIR}. "
                "Add TXT, Markdown, PDF, or DOCX files and run /reindex."
            )

        fingerprint = self._fingerprint(files)
        manifest = self._read_manifest()
        if not force and manifest.get("fingerprint") == fingerprint:
            self.vector_store = self._create_store()
            return f"Knowledge base ready with {manifest.get('chunks', 0)} stored chunks."

        loaded_documents: list[Document] = []
        errors: list[str] = []
        for path in files:
            try:
                loaded_documents.extend(self._load_file(path))
            except Exception as exc:
                errors.append(f"{path.name}: {exc}")

        if not loaded_documents:
            details = "; ".join(errors) if errors else "No readable text was found."
            return f"Knowledge-base indexing failed. {details}"

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(loaded_documents)

        self.vector_store = None
        if CHROMA_DIR.exists():
            shutil.rmtree(CHROMA_DIR)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=COLLECTION_NAME,
            persist_directory=str(CHROMA_DIR),
        )
        MANIFEST_PATH.write_text(
            json.dumps(
                {
                    "fingerprint": fingerprint,
                    "files": [str(path.relative_to(DOCUMENTS_DIR)) for path in files],
                    "chunks": len(chunks),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        message = f"Indexed {len(files)} file(s) into {len(chunks)} searchable chunks."
        if errors:
            message += " Skipped: " + "; ".join(errors)
        return message

    def search(self, question: str, top_k: int = TOP_K) -> str:
        if not question.strip():
            return "Please provide a question for the knowledge base."

        if self.vector_store is None:
            self.index_documents(force=False)
        if self.vector_store is None:
            return "The knowledge base is not available."

        try:
            documents = self.vector_store.similarity_search(question, k=top_k)
        except Exception as exc:
            return f"Knowledge-base search failed: {exc}"

        if not documents:
            return "No relevant information was found in the local documents."

        sections = []
        for index, document in enumerate(documents, start=1):
            source = document.metadata.get("source", "unknown source")
            page = document.metadata.get("page")
            location = f", page {page + 1}" if isinstance(page, int) else ""
            sections.append(
                f"[Source {index}: {source}{location}]\n{document.page_content.strip()}"
            )
        return "\n\n".join(sections)
