"""Safe desktop, utility, web, and RAG tools available to the AI agent."""

from __future__ import annotations

import ast
import datetime as dt
import math
import operator
import os
import random
import shutil
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import pywhatkit
import wikipedia
from langchain.tools import tool

from rag import KnowledgeBase


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _safe_calculate(expression: str) -> float | int:
    """Evaluate arithmetic without eval(), function calls, or variable access."""
    if len(expression) > 200:
        raise ValueError("Expression is too long.")

    def evaluate(node: ast.AST) -> float | int:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > 10 or abs(left) > 1_000_000):
                raise ValueError("Exponent is outside the safe range.")
            return _BINARY_OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            return _UNARY_OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError("Only normal arithmetic numbers and operators are allowed.")

    result = evaluate(ast.parse(expression, mode="eval"))
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Result is not finite.")
    return result


def build_tools(knowledge_base: KnowledgeBase) -> list:
    @tool
    def search_local_documents(question: str) -> str:
        """Search the user's local TXT, Markdown, PDF, and DOCX documents. Use this for questions about uploaded notes, resumes, reports, policies, or project files."""
        return knowledge_base.search(question)

    @tool
    def reindex_local_documents() -> str:
        """Rebuild the local RAG knowledge base after the user explicitly says documents were added, removed, or changed."""
        return knowledge_base.index_documents(force=True)

    @tool
    def get_current_date_and_time() -> str:
        """Return the computer's current local date, day, and time."""
        now = dt.datetime.now().astimezone()
        return now.strftime("%A, %d %B %Y at %I:%M:%S %p %Z")

    @tool
    def calculate(expression: str) -> str:
        """Safely calculate a mathematical expression such as '(24 * 6) / 3'."""
        try:
            return str(_safe_calculate(expression))
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
            return f"Calculation error: {exc}"

    @tool
    def toss_coin() -> str:
        """Toss a virtual coin and return Heads or Tails."""
        return random.choice(["Heads", "Tails"])

    @tool
    def search_wikipedia(topic: str) -> str:
        """Search Wikipedia only when the user explicitly asks for Wikipedia information."""
        cleaned_topic = topic.strip()
        if not cleaned_topic:
            return "Please provide a Wikipedia topic."
        try:
            return wikipedia.summary(
                cleaned_topic,
                sentences=3,
                auto_suggest=True,
                redirect=True,
            )
        except wikipedia.exceptions.DisambiguationError as exc:
            options = ", ".join(exc.options[:5])
            return f"The Wikipedia topic is ambiguous. Possible choices: {options}"
        except wikipedia.exceptions.PageError:
            # The package's auto-suggest occasionally misses a valid page. Search
            # once and retry the strongest result before reporting failure.
            try:
                matches = wikipedia.search(cleaned_topic, results=5)
                if matches:
                    return wikipedia.summary(
                        matches[0],
                        sentences=3,
                        auto_suggest=False,
                        redirect=True,
                    )
            except Exception:
                pass
            return f"No Wikipedia page was found for '{cleaned_topic}'."
        except Exception as exc:
            return f"Wikipedia could not be reached: {exc}"

    @tool
    def open_website(website: str) -> str:
        """Open a website in the default browser only when the user explicitly asks to open it. The input may be a site name or URL."""
        known_sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "stack overflow": "https://stackoverflow.com",
            "linkedin": "https://www.linkedin.com",
            "gmail": "https://mail.google.com",
        }
        value = website.strip().lower()
        url = known_sites.get(value, website.strip())
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "That is not a valid HTTP or HTTPS website."

        webbrowser.open(url)
        return f"Opened {url} in the default browser."

    @tool
    def search_google(query: str) -> str:
        """Open Google search results in the browser only when the user explicitly asks to search the web in their browser."""
        url = f"https://www.google.com/search?q={quote_plus(query.strip())}"
        webbrowser.open(url)
        return f"Opened Google search results for '{query}'."

    @tool
    def play_on_youtube(query: str) -> str:
        """Play a requested song or video on YouTube only when the user explicitly asks to play it."""
        pywhatkit.playonyt(query.strip())
        return f"Playing '{query}' on YouTube."

    @tool
    def open_application(application: str) -> str:
        """Open an allow-listed desktop application only when explicitly requested. Supported apps: VS Code, Notepad, Calculator, File Explorer, and Command Prompt."""
        app = application.strip().lower()
        aliases = {
            "visual studio code": "vscode",
            "vs code": "vscode",
            "code": "vscode",
            "notepad": "notepad",
            "calculator": "calculator",
            "calc": "calculator",
            "file explorer": "explorer",
            "explorer": "explorer",
            "command prompt": "cmd",
            "cmd": "cmd",
        }
        target = aliases.get(app)
        if not target:
            return "Unsupported application. Try VS Code, Notepad, Calculator, File Explorer, or Command Prompt."

        try:
            if os.name == "nt":
                windows_commands = {
                    "notepad": ["notepad.exe"],
                    "calculator": ["calc.exe"],
                    "explorer": ["explorer.exe"],
                    "cmd": ["cmd.exe"],
                }
                if target == "vscode":
                    code_command = shutil.which("code")
                    fallback = Path(os.getenv("LOCALAPPDATA", "")) / "Programs/Microsoft VS Code/Code.exe"
                    if code_command:
                        subprocess.Popen([code_command])
                    elif fallback.exists():
                        os.startfile(str(fallback))  # type: ignore[attr-defined]
                    else:
                        return "VS Code was not found. Add the 'code' command to PATH or install VS Code."
                else:
                    subprocess.Popen(windows_commands[target])
            else:
                linux_commands = {
                    "vscode": ["code"],
                    "notepad": ["gedit"],
                    "calculator": ["gnome-calculator"],
                    "explorer": ["xdg-open", "."],
                    "cmd": ["x-terminal-emulator"],
                }
                subprocess.Popen(linux_commands[target])
            return f"Opening {application}."
        except Exception as exc:
            return f"Could not open {application}: {exc}"

    return [
        search_local_documents,
        reindex_local_documents,
        get_current_date_and_time,
        calculate,
        toss_coin,
        search_wikipedia,
        open_website,
        search_google,
        play_on_youtube,
        open_application,
    ]
