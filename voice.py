"""Voice input and reliable text-to-speech for Velvet.

On Windows, speech output uses the built-in .NET ``System.Speech`` engine in a
fresh hidden PowerShell process for every response.  This deliberately avoids
the common pyttsx3/SAPI5 state bug where the first response speaks and later
responses are silently ignored.

Messages are still processed by one queue worker, so replies never speak over
one another and the CustomTkinter GUI remains responsive.
"""

from __future__ import annotations

import os
import queue
import re
import subprocess
import threading
from typing import Optional

import pyttsx3
import speech_recognition as sr

from config import ASSISTANT_NAME, VOICE_LANGUAGE, VOICE_MAX_CHARS, VOICE_RATE


class VoiceInterface:
    """Microphone input plus queued, repeatable speech output."""

    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self._speech_queue: queue.Queue[Optional[str]] = queue.Queue()
        self._shutdown_event = threading.Event()
        self._speech_thread = threading.Thread(
            target=self._speech_worker,
            name="VelvetSpeechWorker",
            daemon=True,
        )
        self._speech_thread.start()

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        text = re.sub(r"```.*?```", " Code omitted from speech. ", text, flags=re.DOTALL)
        text = re.sub(r"[`*_#>|]", "", text)
        text = re.sub(r"https?://\S+", "link", text)
        return re.sub(r"\s+", " ", text).strip()

    def _prepare_spoken_text(self, text: str) -> str:
        spoken_text = self._clean_for_speech(text)
        if len(spoken_text) > VOICE_MAX_CHARS:
            spoken_text = spoken_text[:VOICE_MAX_CHARS].rsplit(" ", 1)[0]
            spoken_text += ". The complete answer is shown on the screen."
        return spoken_text

    @staticmethod
    def _windows_rate() -> int:
        """Map pyttsx3-style rate (roughly 100-250) to System.Speech -10..10."""
        mapped = round((VOICE_RATE - 175) / 15)
        return max(-10, min(10, mapped))

    def _speak_with_windows_system_speech(self, text: str) -> bool:
        """Speak once with Windows' native System.Speech engine.

        A fresh synthesizer is created per reply.  This is slower than keeping
        one pyttsx3 engine alive, but it reliably speaks the second, third and
        later responses too.
        """
        if os.name != "nt":
            return False

        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Rate = {self._windows_rate()}; "
            "$s.Volume = 100; "
            "$t = [Console]::In.ReadToEnd(); "
            "if (-not [string]::IsNullOrWhiteSpace($t)) { $s.Speak($t) }; "
            "$s.Dispose();"
        )

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                input=text,
                text=True,
                capture_output=True,
                timeout=180,
                creationflags=creationflags,
                check=False,
            )
            if completed.returncode == 0:
                return True

            error = (completed.stderr or completed.stdout or "unknown error").strip()
            print(f"[Voice warning] Windows System.Speech failed: {error}")
        except Exception as exc:
            print(f"[Voice warning] Windows System.Speech failed: {exc}")
        return False

    @staticmethod
    def _speak_with_fresh_pyttsx3(text: str) -> bool:
        """Fallback backend; creates and disposes a fresh engine per message."""
        engine = None
        try:
            try:
                engine = pyttsx3.init("sapi5" if os.name == "nt" else None)
            except Exception:
                engine = pyttsx3.init()

            engine.setProperty("rate", VOICE_RATE)
            voices = engine.getProperty("voices") or []
            if voices:
                engine.setProperty("voice", voices[0].id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return True
        except Exception as exc:
            print(f"[Voice error] pyttsx3 could not speak: {exc}")
            try:
                if engine is not None:
                    engine.stop()
            except Exception:
                pass
            return False

    def _speech_worker(self) -> None:
        """Consume replies sequentially and speak every queued message."""
        while True:
            text = self._speech_queue.get()
            try:
                if text is None:
                    return

                spoken = self._speak_with_windows_system_speech(text)
                if not spoken:
                    self._speak_with_fresh_pyttsx3(text)
            except Exception as exc:
                # Never allow one failed utterance to kill the long-lived worker.
                print(f"[Voice error] Speech worker recovered from: {exc}")
            finally:
                self._speech_queue.task_done()

    def speak(self, text: str) -> None:
        """Queue a response for speech without blocking the GUI."""
        print(f"\n{ASSISTANT_NAME}: {text}\n")
        spoken_text = self._prepare_spoken_text(text)
        if spoken_text and not self._shutdown_event.is_set():
            self._speech_queue.put(spoken_text)

    def wait_until_done(self) -> None:
        """Wait until all queued speech is complete (mainly for diagnostics)."""
        self._speech_queue.join()

    def shutdown(self) -> None:
        """Stop the speech worker when the application closes."""
        if self._shutdown_event.is_set():
            return
        self._shutdown_event.set()
        self._speech_queue.put(None)
        self._speech_thread.join(timeout=2.0)

    def listen(self) -> Optional[str]:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=20)
        except sr.WaitTimeoutError:
            print("No speech detected. Please try again.")
            return None
        except Exception as exc:
            print(f"Microphone is unavailable: {exc}")
            return None

        try:
            print("Recognizing...")
            query = self.recognizer.recognize_google(audio, language=VOICE_LANGUAGE)
            print(f"You: {query}")
            return query.strip()
        except sr.UnknownValueError:
            print("I could not understand the audio.")
        except sr.RequestError as exc:
            print(f"Speech recognition service error: {exc}")
        return None
