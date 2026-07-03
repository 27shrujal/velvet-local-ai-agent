<img width="3302" height="1967" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/5e50b28d-a4fb-4cf4-b76b-4d250a1d0126" />💜 Professional Velvet introduction
✨ Complete features
🧠 Models and technologies
🏗️ Project architecture
📚 RAG explanation
🗂️ ChromaDB explanation
🤖 Qwen and embedding model details
📁 Folder structure
🚀 Automatic and manual installation
🔧 .env configuration
📄 Document upload process
💬 Example commands
🎙️ Voice input/output
🌐 Offline vs online features
🔐 Security and privacy
🚫 Files not to upload
✅ Files safe to upload
⚠️ Current limitations
🛣️ Future improvements
🧪 Troubleshooting
👨‍💻 Your author information
📜 All Rights Reserved copyright
⭐ GitHub support section

## 🏗️ Velvet System Architecture

```mermaid
flowchart TD
    U[👤 User] --> I[🖥️ Velvet GUI<br/>CustomTkinter]
    I --> V[🎙️ Voice / Text Input Handler]
    V --> R[🧠 Velvet Agent Router]

    R -->|General Question| G[🤖 General Agent]
    R -->|Tool or Action Request| T[🧰 Tool Agent]

    G --> LLM[🧠 Qwen2.5:3B<br/>via Ollama]
    T --> LLM

    T --> TOOLS[🔧 Tools Layer]

    TOOLS --> RAG[📚 RAG Search]
    TOOLS --> WEB[🌐 Browser / Wikipedia / YouTube]
    TOOLS --> SYS[💻 Desktop App Launcher]
    TOOLS --> CALC[🧮 Safe Calculator]
    TOOLS --> TIME[🕒 Date and Time]

    DOCS[📄 Local Documents<br/>PDF / DOCX / TXT / MD] --> RAG
    RAG --> EMB[📌 Embedding Model<br/>nomic-embed-text]
    EMB --> CHROMA[(🗂️ ChromaDB)]

    CHROMA --> LLM
    LLM --> OUT[💬 Final Response]

    OUT --> GUI[🪟 Chat Output in GUI]
    OUT --> SPEAK[🔊 Voice Output]
