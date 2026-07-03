# Security Policy

## Publishing Safely

Do not commit or upload:

- `.env`
- API keys, tokens, passwords, certificates, or private keys
- Files inside `documents/` other than the included sample
- Generated files inside `chroma_db/`
- `.venv/`, `__pycache__/`, logs, or local backup archives
- Screenshots containing private information

## Privacy Notes

The local LLM and RAG components run through Ollama. Voice input currently uses Google's speech-recognition service, and browser/Wikipedia/YouTube tools require internet access.

## Reporting a Vulnerability

Please open a GitHub issue without including secrets, private documents, exploit payloads, or personal data. For sensitive reports, use a private contact method listed on the repository owner's GitHub profile.
