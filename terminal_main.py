"""Terminal entry point for the Velvet desktop AI agent."""

from __future__ import annotations

import datetime as dt
import sys

from config import ASSISTANT_NAME, EMBEDDING_MODEL, LLM_MODEL, USER_NAME
from rag import KnowledgeBase
from velvet_agent import VelvetAgent
from voice import VoiceInterface

HELP_TEXT = f"""
Commands:
  /voice    Switch to voice input
  /text     Switch to text input
  /reindex  Rebuild RAG index from the documents folder
  /new      Start a new conversation memory
  /help     Show this help
  /exit     Close {ASSISTANT_NAME}

Examples:
  Ask my documents: What skills are listed in my resume?
  Agent tool: Open YouTube and play Python tutorial.
  Agent tool: Calculate (1250 * 18) / 100.
  General chat: Explain RAG in simple words.
""".strip()


def greeting() -> str:
    hour = dt.datetime.now().hour
    if hour < 12:
        part = "Good morning"
    elif hour < 18:
        part = "Good afternoon"
    else:
        part = "Good evening"
    return f"{part}, {USER_NAME}. I am {ASSISTANT_NAME}, your desktop AI agent."


def choose_initial_mode() -> str:
    print("\nSelect input mode:")
    print("1. Voice")
    print("2. Text")
    choice = input("Choice [2]: ").strip()
    return "voice" if choice == "1" else "text"


def main() -> int:
    voice = VoiceInterface()
    print(f"\nStarting {ASSISTANT_NAME} with LLM '{LLM_MODEL}' and embeddings '{EMBEDDING_MODEL}'...")

    try:
        knowledge_base = KnowledgeBase()
        print(knowledge_base.index_documents(force=False))
        agent = VelvetAgent(knowledge_base)
    except Exception as exc:
        print(f"\n{ASSISTANT_NAME} could not connect to the local Ollama models.")
        print(f"Technical error: {exc}")
        print("\nCheck that Ollama is running, then execute:")
        print(f"  ollama pull {LLM_MODEL}")
        print(f"  ollama pull {EMBEDDING_MODEL}")
        return 1

    voice.speak(greeting())
    print(HELP_TEXT)
    mode = choose_initial_mode()

    while True:
        if mode == "voice":
            user_input = voice.listen()
            if not user_input:
                continue
        else:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                user_input = "/exit"

        if not user_input:
            continue

        command = user_input.lower().strip()
        if command in {"/exit", "exit", "quit", "goodbye"}:
            voice.speak("Goodbye. Have a good day.")
            break
        if command == "/voice":
            mode = "voice"
            voice.speak("Voice input enabled.")
            continue
        if command == "/text":
            mode = "text"
            voice.speak("Text input enabled.")
            continue
        if command == "/help":
            print(HELP_TEXT)
            continue
        if command == "/new":
            agent.new_conversation()
            voice.speak("Started a new conversation.")
            continue
        if command == "/reindex":
            voice.speak(knowledge_base.index_documents(force=True))
            continue

        try:
            response = agent.ask(user_input)
        except Exception as exc:
            response = (
                "I could not complete that request. Make sure Ollama is running and the selected "
                f"model supports tool calling. Technical error: {exc}"
            )
        voice.speak(response)

    return 0


if __name__ == "__main__":
    sys.exit(main())
