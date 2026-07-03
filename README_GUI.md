# Velvet — LLM-Powered Desktop AI Agent with RAG

Velvet is a private, local desktop AI assistant with an attractive purple-themed GUI, voice input/output, LangGraph agent tools, conversation memory, and document RAG.

## Start on Windows

1. Install Python 3.10 and Ollama.
2. Extract this project.
3. Double-click `START_VELVET.bat`.

The first launch creates `.venv`, installs packages, starts Ollama, downloads missing models, builds the RAG index, and opens the GUI.

## Main GUI features

- Velvet-branded modern dark interface
- Text chat and microphone input
- Optional spoken responses
- PDF, DOCX, TXT and Markdown upload
- Local RAG with ChromaDB
- New conversation memory
- Website, YouTube and approved desktop-app tools
- Velvet-inspired dark interface and local-mode status badges

## Manual terminal command

```powershell
cd .\velvet_ai_agent_gui
.\START_VELVET.bat
```

## July 2026 reliability update

- Fixed chat bubble alignment and off-screen assistant responses.
- Normal knowledge questions now use Velvet's LLM directly instead of unnecessarily calling Wikipedia.
- Desktop, RAG, time, calculator, browser, and explicit Wikipedia requests still use agent tools.
- Follow-up questions such as “why?” retain the correct conversation path.
