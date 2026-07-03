"""Modern desktop GUI entry point for the Velvet AI Agent."""

from __future__ import annotations

import datetime as dt
import os
import shutil
import threading
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk
from PIL import Image

from config import (
    ASSISTANT_NAME,
    BASE_DIR,
    DOCUMENTS_DIR,
    EMBEDDING_MODEL,
    LLM_MODEL,
    MODEL_DISPLAY_NAME,
    USER_NAME,
)
from rag import KnowledgeBase, SUPPORTED_EXTENSIONS
from velvet_agent import VelvetAgent
from voice import VoiceInterface


# Velvet-inspired theme palette.
COLORS = {
    "app_bg": "#09060F",
    "sidebar": "#120B1D",
    "panel": "#0E0917",
    "card": "#1B1128",
    "card_hover": "#251638",
    "border": "#352044",
    "primary": "#8B5CF6",
    "primary_hover": "#7C3AED",
    "accent": "#C084FC",
    "user_bubble": "#6D28D9",
    "assistant_bubble": "#1D132A",
    "text": "#F8F5FF",
    "muted": "#A89CB8",
    "success": "#34D399",
    "warning": "#FBBF24",
    "error": "#FB7185",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VelvetGUI(ctk.CTk):
    """Thread-safe desktop chat interface for the local Velvet agent."""

    def __init__(self) -> None:
        super().__init__(fg_color=COLORS["app_bg"])

        self.title(f"{ASSISTANT_NAME} — Private Desktop AI")
        self.geometry("1180x780")
        self.minsize(980, 660)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        icon_path = BASE_DIR / "assets" / "velvet.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.voice = VoiceInterface()
        self.knowledge_base: KnowledgeBase | None = None
        self.agent: VelvetAgent | None = None
        self.is_busy = False
        self.is_listening = False
        self.voice_output_enabled = ctk.BooleanVar(value=True)
        self._welcome_frame: ctk.CTkFrame | None = None

        self._configure_layout()
        self._build_sidebar()
        self._build_main_panel()
        self._set_status("Starting local AI...", "warning")
        self.after(250, self._initialize_agent_async)

    def _configure_layout(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _load_logo(self, size: int) -> ctk.CTkImage | None:
        path = BASE_DIR / "assets" / "velvet_logo.png"
        if not path.exists():
            return None
        try:
            image = Image.open(path)
            return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
        except Exception:
            return None

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(
            self,
            width=270,
            corner_radius=0,
            fg_color=COLORS["sidebar"],
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(8, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=20, pady=(26, 20), sticky="ew")
        brand.grid_columnconfigure(1, weight=1)

        logo = self._load_logo(54)
        if logo:
            logo_label = ctk.CTkLabel(brand, text="", image=logo)
            logo_label.image = logo
        else:
            logo_label = ctk.CTkLabel(
                brand,
                text="V",
                width=54,
                height=54,
                corner_radius=27,
                fg_color=COLORS["primary"],
                font=ctk.CTkFont(size=28, weight="bold"),
                text_color="white",
            )
        logo_label.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="w")

        ctk.CTkLabel(
            brand,
            text="VELVET",
            font=ctk.CTkFont(size=27, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=1, sticky="sw")

        ctk.CTkLabel(
            brand,
            text="Private Desktop AI",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=1, sticky="nw")

        self.new_chat_button = ctk.CTkButton(
            sidebar,
            text="＋  New conversation",
            height=46,
            corner_radius=14,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._new_conversation,
        )
        self.new_chat_button.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="ew")

        ctk.CTkLabel(
            sidebar,
            text="KNOWLEDGE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, padx=23, pady=(8, 5), sticky="w")

        self.upload_button = self._sidebar_button(sidebar, "↑  Upload documents", self._upload_documents)
        self.upload_button.grid(row=3, column=0, padx=18, pady=5, sticky="ew")

        self.reindex_button = self._sidebar_button(sidebar, "↻  Rebuild RAG index", self._reindex_documents)
        self.reindex_button.grid(row=4, column=0, padx=18, pady=5, sticky="ew")

        self.folder_button = self._sidebar_button(sidebar, "▣  Open documents folder", self._open_documents_folder)
        self.folder_button.grid(row=5, column=0, padx=18, pady=5, sticky="ew")

        voice_card = ctk.CTkFrame(
            sidebar,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        voice_card.grid(row=6, column=0, padx=18, pady=(18, 8), sticky="ew")
        voice_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            voice_card,
            text="Voice responses",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=(14, 6), pady=(12, 2), sticky="w")
        ctk.CTkLabel(
            voice_card,
            text="Velvet speaks answers aloud",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, padx=(14, 6), pady=(0, 12), sticky="w")

        self.voice_switch = ctk.CTkSwitch(
            voice_card,
            text="",
            variable=self.voice_output_enabled,
            onvalue=True,
            offvalue=False,
            progress_color=COLORS["primary"],
            button_hover_color=COLORS["accent"],
            width=42,
        )
        self.voice_switch.grid(row=0, column=1, rowspan=2, padx=(4, 12), pady=12)

        system_card = ctk.CTkFrame(
            sidebar,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        system_card.grid(row=9, column=0, padx=18, pady=(8, 12), sticky="sew")
        system_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            system_card,
            text="LOCAL SYSTEM",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["accent"],
        ).grid(row=0, column=0, padx=14, pady=(13, 6), sticky="w")

        ctk.CTkLabel(
            system_card,
            text=f"MODEL   {MODEL_DISPLAY_NAME}\nENGINE  {LLM_MODEL}\nRAG     {EMBEDDING_MODEL}",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, padx=14, pady=(0, 7), sticky="w")

        self.document_count_label = ctk.CTkLabel(
            system_card,
            text=f"{self._document_count()} documents available",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["success"],
        )
        self.document_count_label.grid(row=2, column=0, padx=14, pady=(0, 13), sticky="w")

        ctk.CTkLabel(
            sidebar,
            text="Local • Private • No paid API",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted"],
        ).grid(row=10, column=0, padx=18, pady=(0, 16))

    def _sidebar_button(self, parent: ctk.CTkFrame, text: str, command: Callable[[], None]) -> ctk.CTkButton:
        return ctk.CTkButton(
            parent,
            text=text,
            height=42,
            anchor="w",
            corner_radius=12,
            fg_color="transparent",
            hover_color=COLORS["card_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
            command=command,
        )

    def _build_main_panel(self) -> None:
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["panel"])
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(main, height=88, corner_radius=0, fg_color=COLORS["panel"])
        header.grid(row=0, column=0, sticky="ew", padx=26, pady=(14, 0))
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        greeting = self._greeting_text()
        ctk.CTkLabel(
            header,
            text=f"{greeting}, {USER_NAME}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=2, pady=(8, 0), sticky="w")

        ctk.CTkLabel(
            header,
            text=f"Ask {ASSISTANT_NAME} anything, or search your private documents.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        ).grid(row=1, column=0, padx=2, pady=(0, 8), sticky="w")

        status_frame = ctk.CTkFrame(
            header,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        status_frame.grid(row=0, column=1, rowspan=2, padx=(10, 12), pady=17)

        self.status_dot = ctk.CTkLabel(status_frame, text="●", width=18, text_color=COLORS["warning"])
        self.status_dot.grid(row=0, column=0, padx=(12, 3), pady=9)
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Starting...",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["muted"],
        )
        self.status_label.grid(row=0, column=1, padx=(0, 12), pady=9)

        mode_badge = ctk.CTkFrame(
            header,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        mode_badge.grid(row=0, column=2, rowspan=2, padx=(0, 2), pady=17)
        ctk.CTkLabel(
            mode_badge,
            text="✦  LOCAL MODE",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(padx=14, pady=9)

        self.activity_bar = ctk.CTkProgressBar(
            main,
            height=3,
            corner_radius=0,
            mode="indeterminate",
            progress_color=COLORS["primary"],
            fg_color=COLORS["panel"],
        )
        self.activity_bar.grid(row=0, column=0, sticky="sew", padx=26)
        self.activity_bar.set(0)

        self.chat_frame = ctk.CTkScrollableFrame(
            main,
            corner_radius=18,
            fg_color=COLORS["app_bg"],
            border_width=1,
            border_color=COLORS["border"],
            scrollbar_button_color=COLORS["card"],
            scrollbar_button_hover_color=COLORS["primary"],
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=26, pady=(12, 10))
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self._build_welcome_state()

        input_panel = ctk.CTkFrame(
            main,
            corner_radius=20,
            fg_color=COLORS["card"],
            border_width=1,
            border_color=COLORS["border"],
        )
        input_panel.grid(row=2, column=0, sticky="ew", padx=26, pady=(0, 12))
        input_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            input_panel,
            text="MESSAGE VELVET",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORS["accent"],
        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 3), sticky="w")

        self.input_box = ctk.CTkTextbox(
            input_panel,
            height=76,
            corner_radius=13,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["panel"],
            text_color=COLORS["text"],
            wrap="word",
            font=ctk.CTkFont(size=14),
        )
        self.input_box.grid(row=1, column=0, rowspan=2, sticky="ew", padx=(14, 8), pady=(4, 14))
        self.input_box.bind("<Control-Return>", self._send_from_event)

        self.mic_button = ctk.CTkButton(
            input_panel,
            text="●  Mic",
            width=96,
            height=36,
            corner_radius=12,
            fg_color=COLORS["card_hover"],
            hover_color=COLORS["border"],
            border_width=1,
            border_color=COLORS["border"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._listen_async,
            state="disabled",
        )
        self.mic_button.grid(row=1, column=1, padx=(0, 12), pady=(5, 4), sticky="se")

        self.send_button = ctk.CTkButton(
            input_panel,
            text="Send  ↑",
            width=96,
            height=36,
            corner_radius=12,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._send_message,
            state="disabled",
        )
        self.send_button.grid(row=2, column=1, padx=(0, 12), pady=(4, 14), sticky="ne")

        ctk.CTkLabel(
            main,
            text="Ctrl + Enter to send   •   PDF, DOCX, TXT and MD supported for private RAG",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["muted"],
        ).grid(row=3, column=0, pady=(0, 9))

    def _build_welcome_state(self) -> None:
        self._welcome_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self._welcome_frame.grid(row=0, column=0, sticky="nsew", padx=34, pady=34)
        for column in range(3):
            self._welcome_frame.grid_columnconfigure(column, weight=1)

        logo = self._load_logo(84)
        if logo:
            logo_label = ctk.CTkLabel(self._welcome_frame, text="", image=logo)
            logo_label.image = logo
        else:
            logo_label = ctk.CTkLabel(
                self._welcome_frame,
                text="V",
                width=84,
                height=84,
                corner_radius=42,
                fg_color=COLORS["primary"],
                text_color="white",
                font=ctk.CTkFont(size=42, weight="bold"),
            )
        logo_label.grid(row=0, column=0, columnspan=3, pady=(18, 12))

        ctk.CTkLabel(
            self._welcome_frame,
            text=f"Meet {ASSISTANT_NAME}",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"],
        ).grid(row=1, column=0, columnspan=3)

        ctk.CTkLabel(
            self._welcome_frame,
            text="Your local LLM-powered desktop agent with voice, tools and private document intelligence.",
            wraplength=620,
            justify="center",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["muted"],
        ).grid(row=2, column=0, columnspan=3, pady=(5, 24))

        prompts = [
            ("Ask anything", "Explain RAG in simple words."),
            ("Search documents", "Summarize the documents in my knowledge base."),
            ("Use a tool", "Open YouTube in my browser."),
        ]
        for column, (title, prompt) in enumerate(prompts):
            card = ctk.CTkButton(
                self._welcome_frame,
                text=f"{title}\n\n{prompt}",
                height=116,
                corner_radius=16,
                fg_color=COLORS["card"],
                hover_color=COLORS["card_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(size=12),
                command=lambda value=prompt: self._use_quick_prompt(value),
            )
            card.grid(row=3, column=column, padx=7, pady=4, sticky="ew")

    def _dismiss_welcome(self) -> None:
        if self._welcome_frame and self._welcome_frame.winfo_exists():
            self._welcome_frame.destroy()
        self._welcome_frame = None

    @staticmethod
    def _greeting_text() -> str:
        hour = dt.datetime.now().hour
        if hour < 12:
            return "Good morning"
        if hour < 18:
            return "Good afternoon"
        return "Good evening"

    @staticmethod
    def _document_count() -> int:
        return sum(
            1
            for path in DOCUMENTS_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    def _refresh_document_count(self) -> None:
        self.document_count_label.configure(text=f"{self._document_count()} documents available")

    def _use_quick_prompt(self, prompt: str) -> None:
        if not self.agent or self.is_busy:
            return
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", prompt)
        self._send_message()

    def _initialize_agent_async(self) -> None:
        self._set_busy(True)
        self._run_background(self._initialize_agent, self._on_agent_ready, self._on_agent_error)

    def _initialize_agent(self) -> tuple[KnowledgeBase, VelvetAgent, str]:
        knowledge_base = KnowledgeBase()
        index_message = knowledge_base.index_documents(force=False)
        agent = VelvetAgent(knowledge_base)
        return knowledge_base, agent, index_message

    def _on_agent_ready(self, result: tuple[KnowledgeBase, VelvetAgent, str]) -> None:
        self.knowledge_base, self.agent, _index_message = result
        self._set_busy(False)
        self._set_status("Online & ready", "ready")
        self._refresh_document_count()
        self.input_box.focus_set()

    def _on_agent_error(self, exc: Exception) -> None:
        self._set_busy(False)
        self._set_status("Ollama connection failed", "error")
        self._dismiss_welcome()
        self._add_message(
            "assistant",
            "I could not connect to Ollama. Make sure Ollama is installed and running, then run:\n"
            f"ollama pull {LLM_MODEL}\n"
            f"ollama pull {EMBEDDING_MODEL}\n\n"
            f"Technical error: {exc}",
        )

    def _send_from_event(self, _event: object) -> str:
        self._send_message()
        return "break"

    def _send_message(self) -> None:
        if self.is_busy or not self.agent:
            return

        message = self.input_box.get("1.0", "end").strip()
        if not message:
            return

        self._dismiss_welcome()
        self.input_box.delete("1.0", "end")
        self._add_message("user", message)
        self._set_busy(True)
        self._set_status("Thinking...", "warning")
        self._run_background(
            lambda: self.agent.ask(message),
            self._on_agent_response,
            self._on_request_error,
        )

    def _on_agent_response(self, response: str) -> None:
        self._add_message("assistant", response)
        self._set_busy(False)
        self._set_status("Online & ready", "ready")
        self.input_box.focus_set()
        if self.voice_output_enabled.get():
            # VoiceInterface already owns a dedicated speech worker thread.
            # Queueing here avoids the Windows SAPI5 "speaks only once" issue.
            self.voice.speak(response)

    def _on_request_error(self, exc: Exception) -> None:
        self._dismiss_welcome()
        self._add_message(
            "assistant",
            "I could not complete the request. Confirm that Ollama is running.\n\n"
            f"Technical error: {exc}",
        )
        self._set_busy(False)
        self._set_status("Request failed", "error")

    def _listen_async(self) -> None:
        if self.is_busy or self.is_listening or not self.agent:
            return
        self.is_listening = True
        self.mic_button.configure(state="disabled", text="Listening...")
        self._set_status("Listening...", "warning")
        self._run_background(self.voice.listen, self._on_voice_result, self._on_voice_error)

    def _on_voice_result(self, text: str | None) -> None:
        self.is_listening = False
        self.mic_button.configure(state="normal", text="●  Mic")
        if not text:
            self._set_status("No speech detected", "error")
            return
        self.input_box.delete("1.0", "end")
        self.input_box.insert("1.0", text)
        self._set_status("Voice recognized", "ready")
        self._send_message()

    def _on_voice_error(self, exc: Exception) -> None:
        self.is_listening = False
        self.mic_button.configure(state="normal", text="●  Mic")
        self._set_status("Microphone error", "error")
        self._dismiss_welcome()
        self._add_message("assistant", f"The microphone could not be used: {exc}")

    def _new_conversation(self) -> None:
        if not self.agent or self.is_busy:
            return
        self.agent.new_conversation()
        for child in self.chat_frame.winfo_children():
            child.destroy()
        self._welcome_frame = None
        self._build_welcome_state()
        self._set_status("New conversation", "ready")
        self.input_box.delete("1.0", "end")
        self.input_box.focus_set()

    def _upload_documents(self) -> None:
        selected = filedialog.askopenfilenames(
            title=f"Choose documents for {ASSISTANT_NAME} RAG",
            filetypes=[
                ("Supported documents", "*.pdf *.docx *.txt *.md"),
                ("PDF files", "*.pdf"),
                ("Word documents", "*.docx"),
                ("Text files", "*.txt *.md"),
            ],
        )
        if not selected:
            return

        copied: list[str] = []
        skipped: list[str] = []
        for source_name in selected:
            source = Path(source_name)
            if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
                skipped.append(source.name)
                continue

            destination = DOCUMENTS_DIR / source.name
            counter = 1
            while destination.exists() and destination.resolve() != source.resolve():
                destination = DOCUMENTS_DIR / f"{source.stem}_{counter}{source.suffix}"
                counter += 1
            try:
                if destination.resolve() != source.resolve():
                    shutil.copy2(source, destination)
                copied.append(destination.name)
            except OSError:
                skipped.append(source.name)

        if copied:
            self._dismiss_welcome()
            self._add_message("assistant", "Added to the private knowledge base:\n" + "\n".join(copied))
            self._refresh_document_count()
            self._reindex_documents()
        if skipped:
            messagebox.showwarning("Some files were skipped", "\n".join(skipped))

    def _reindex_documents(self) -> None:
        if self.is_busy or not self.knowledge_base:
            return
        self._set_busy(True)
        self._set_status("Building RAG index...", "warning")
        self._run_background(
            lambda: self.knowledge_base.index_documents(force=True),
            self._on_reindex_complete,
            self._on_request_error,
        )

    def _on_reindex_complete(self, message: str) -> None:
        self._dismiss_welcome()
        self._add_message("assistant", message)
        self._refresh_document_count()
        self._set_busy(False)
        self._set_status("RAG index ready", "ready")

    def _open_documents_folder(self) -> None:
        try:
            if os.name == "nt":
                os.startfile(str(DOCUMENTS_DIR))  # type: ignore[attr-defined]
            else:
                import subprocess

                subprocess.Popen(["xdg-open", str(DOCUMENTS_DIR)])
        except Exception as exc:
            messagebox.showerror("Could not open folder", str(exc))

    def _add_message(self, role: str, text: str) -> None:
        """Render a responsive chat row without pushing bubbles outside the viewport."""
        row = len(self.chat_frame.winfo_children())
        is_user = role == "user"

        # The outer row always occupies the complete chat width.  A small inner
        # group is packed left/right, which prevents the large empty grid column
        # bug that previously pushed assistant messages off-screen.
        outer = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        outer.grid(row=row, column=0, sticky="ew", padx=16, pady=8)

        message_group = ctk.CTkFrame(outer, fg_color="transparent")
        message_group.pack(side="right" if is_user else "left", anchor="n")

        avatar_text = "YOU" if is_user else "V"
        avatar = ctk.CTkLabel(
            message_group,
            text=avatar_text,
            width=38,
            height=38,
            corner_radius=19,
            fg_color=COLORS["user_bubble"] if is_user else COLORS["primary"],
            text_color="white",
            font=ctk.CTkFont(size=10 if is_user else 17, weight="bold"),
        )

        bubble = ctk.CTkFrame(
            message_group,
            corner_radius=17,
            fg_color=COLORS["user_bubble"] if is_user else COLORS["assistant_bubble"],
            border_width=0 if is_user else 1,
            border_color=COLORS["border"],
        )

        if is_user:
            bubble.grid(row=0, column=0, sticky="ne", padx=(0, 10))
            avatar.grid(row=0, column=1, sticky="ne")
        else:
            avatar.grid(row=0, column=0, sticky="nw")
            bubble.grid(row=0, column=1, sticky="nw", padx=(10, 0))

        # 560px fits comfortably at the minimum supported application width and
        # still keeps longer answers readable.
        label = ctk.CTkLabel(
            bubble,
            text=text,
            justify="left",
            anchor="w",
            wraplength=560,
            font=ctk.CTkFont(size=14),
            text_color="white" if is_user else COLORS["text"],
        )
        label.pack(padx=16, pady=(12, 6), anchor="w")

        timestamp = dt.datetime.now().strftime("%I:%M %p")
        meta = ctk.CTkLabel(
            bubble,
            text=("You" if is_user else ASSISTANT_NAME) + f"  •  {timestamp}",
            font=ctk.CTkFont(size=9),
            text_color="#DDD6FE" if is_user else COLORS["muted"],
        )
        meta.pack(padx=16, pady=(0, 10), anchor="e" if is_user else "w")

        self.after(60, lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def _set_busy(self, busy: bool) -> None:
        self.is_busy = busy
        state = "disabled" if busy or not self.agent else "normal"
        self.send_button.configure(state=state)
        self.mic_button.configure(state=state)
        self.new_chat_button.configure(state=state)
        self.upload_button.configure(state="disabled" if busy else "normal")
        self.reindex_button.configure(state="disabled" if busy or not self.knowledge_base else "normal")

        if busy:
            self.activity_bar.start()
        else:
            self.activity_bar.stop()
            self.activity_bar.set(0)

    def _set_status(self, text: str, kind: str) -> None:
        color = {
            "ready": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["error"],
        }.get(kind, COLORS["muted"])
        self.status_dot.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)

    def _run_background(
        self,
        task: Callable[[], object],
        on_success: Callable[[object], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        def runner() -> None:
            try:
                result = task()
            except Exception as exc:
                traceback.print_exc()
                self.after(0, lambda: on_error(exc))
            else:
                self.after(0, lambda: on_success(result))

        threading.Thread(target=runner, daemon=True).start()

    def _on_close(self) -> None:
        self.voice.shutdown()
        self.destroy()


if __name__ == "__main__":
    app = VelvetGUI()
    app.mainloop()
