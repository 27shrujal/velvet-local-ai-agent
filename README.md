# Velvet — Local LLM-Powered Desktop AI Agent with RAG

Velvet is a privacy-focused Windows desktop AI agent built with Python. It combines a modern CustomTkinter interface, a local Ollama LLM, LangChain/LangGraph tool execution, conversation memory, voice input/output, and Retrieval-Augmented Generation (RAG) over private documents.

> Velvet is the product and assistant name. The default local language model is `qwen2.5:3b`, and document embeddings are generated with `nomic-embed-text`.

## Features

- Modern desktop chat GUI with Velvet branding
- Local LLM responses through Ollama
- Voice input and spoken responses
- RAG over PDF, DOCX, TXT, and Markdown files
- ChromaDB vector storage for semantic document search
- LangGraph-backed conversation memory
- Safe calculator based on Python AST parsing
- Explicit Wikipedia, Google, YouTube, and browser tools
- Allow-listed desktop application launcher
- Text-only terminal mode
- One-click Windows setup and startup scripts

## Architecture

```text
Voice or text input
        ↓
CustomTkinter GUI
        ↓
Velvet router
        ├── General agent → qwen2.5:3b through Ollama
        └── Tool agent
              ├── RAG → nomic-embed-text + ChromaDB
              ├── Calculator
              ├── Browser / Google / YouTube
              ├── Wikipedia
              └── Allow-listed Windows applications
        ↓
Final text response + optional speech output
```

## Models

| Component | Default | Purpose |
|---|---|---|
| Main LLM | `qwen2.5:3b` | Conversation, reasoning, tool selection, and answer generation |
| Embedding model | `nomic-embed-text` | Converts document chunks and questions into vectors for semantic search |
| Runtime | Ollama | Runs both models locally without a paid cloud LLM API |

`qwen2.5:3b` is used because it is relatively lightweight and practical for CPU-based laptops compared with larger local models. You can replace it in `.env` with another Ollama model that supports the required workflow.

## Technology Stack

- Python 3.10
- CustomTkinter and Pillow
- Ollama
- LangChain and LangGraph
- ChromaDB
- `qwen2.5:3b`
- `nomic-embed-text`
- SpeechRecognition
- Windows `System.Speech` with `pyttsx3` fallback
- PyPDF and docx2txt

## Project Structure

```text
velvet-ai-agent/
├── main.py                       # Desktop GUI and interaction flow
├── velvet_agent.py               # LLM agents, routing, prompts, and memory
├── agent_tools.py                # RAG, calculator, browser, and app tools
├── rag.py                        # Loading, chunking, embeddings, and ChromaDB
├── voice.py                      # Speech recognition and speech output
├── config.py                     # Central configuration
├── terminal_main.py              # Optional terminal interface
├── voice_test.py                 # Repeated speech-output test
├── requirements.txt
├── .env.example                  # Public configuration template
├── .gitignore
├── START_VELVET.bat              # One-click Windows launcher
├── TEST_VOICE.bat                # Voice test launcher
├── setup_windows.bat
├── run_windows.bat
├── RUN_TERMINAL_VERSION.bat
├── assets/
│   ├── velvet_logo.png
│   └── velvet.ico
├── documents/
│   ├── .gitkeep
│   └── about_project.txt         # Harmless example document
└── chroma_db/
    └── .gitkeep                  # Generated database is not committed
```

## Prerequisites

- Windows 10 or newer
- Python 3.10 with the Python launcher enabled
- Ollama installed and available in `PATH`
- Internet access for the first model/package download
- A microphone only when voice input is required

## Quick Start on Windows

1. Clone or download this repository.
2. Open the project folder.
3. Run:

```powershell
.\START_VELVET.bat
```

The launcher will:

1. Create a local `.venv`
2. Install Python dependencies
3. Create `.env` from `.env.example` when needed
4. Start Ollama
5. Download missing models
6. Open the Velvet GUI

The first run can take time because the models must be downloaded.

## Manual Setup

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama serve
```

In another terminal:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## Configuration

Copy `.env.example` to `.env` and update local settings:

```env
MODEL_DISPLAY_NAME=Velvet
LLM_MODEL=qwen2.5:3b
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
COLLECTION_NAME=velvet_documents
ASSISTANT_NAME=Velvet
USER_NAME=User
VOICE_LANGUAGE=en-in
VOICE_RATE=175
TOP_K=4
```

Do not commit `.env`, especially if API keys or private values are added later.

## Using RAG

1. Open Velvet.
2. Use **Upload documents**, or place files inside `documents/`.
3. Add PDF, DOCX, TXT, or Markdown files.
4. Click **Rebuild RAG index**.
5. Ask a document-specific question, for example:

```text
What Python skills are mentioned in my resume?
Summarize my project report.
Which technologies are listed in my documents?
```

RAG processing:

```text
Document → text extraction → chunks → embeddings → ChromaDB
Question → embedding → similarity search → relevant chunks → LLM answer
```

The generated Chroma database is local and excluded from Git because it can contain document text, metadata, and embeddings.

## Voice Test

Run:

```powershell
.\TEST_VOICE.bat
```

This tests multiple spoken messages before launching the full application.

## Terminal Mode

```powershell
.\RUN_TERMINAL_VERSION.bat
```

Available commands include `/voice`, `/text`, `/reindex`, `/new`, `/help`, and `/exit`.

## Security and Privacy

Velvet is designed to reduce unnecessary data exposure, but it should not be described as fully offline in every mode.

- The LLM and RAG workflow run locally through Ollama.
- Private documents and the generated ChromaDB should remain on the user's computer.
- No paid cloud LLM API key is required by default.
- Desktop application launching is restricted to an allow-list.
- Calculator expressions are parsed with a restricted AST evaluator instead of direct `eval()`.
- Retrieved document text is treated as untrusted context, not as executable instructions.
- Microphone recognition currently uses Google's speech-recognition service and therefore requires internet access and may send captured audio for transcription.
- Wikipedia, Google, and YouTube tools require internet access.

Before publishing:

- Never upload `.env`
- Never upload personal PDFs, resumes, reports, certificates, or private documents
- Never upload `chroma_db/` generated files
- Never upload `.venv/`, `__pycache__/`, logs, or local backups
- Review every file for keys, tokens, passwords, email addresses, and absolute local paths

## Known Limitations

- Performance depends on CPU, RAM, and model size.
- Small local models may occasionally choose an incorrect tool or produce an inaccurate answer.
- Voice input is not fully offline in the current version.
- Conversation memory is stored in memory and resets when the application closes.
- RAG quality depends on document text quality and successful extraction.

## Future Improvements

- Fully offline speech-to-text using Whisper
- Persistent conversation history
- Streaming responses
- Source citations as clickable document links
- Additional permission controls for tools
- Automated tests and continuous integration
- Support for more local models

## Author

**Shrujal Satasiya**

Built as a Python, LLM, RAG, and AI Agent portfolio project.

## Disclaimer

This project is intended for learning and portfolio use. Review tool permissions and privacy requirements before using it with confidential or production data.
