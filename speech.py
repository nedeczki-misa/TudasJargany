"""Offline, Windows-os angol kiejtes a feladatgombokhoz."""

from __future__ import annotations

import base64
import shutil
import subprocess
import threading
import time


class EnglishSpeaker:
    """A Windows System.Speech hangjat inditja nem blokkolva."""

    def __init__(self) -> None:
        self._powershell = shutil.which("powershell.exe") or shutil.which("powershell")
        self._process: subprocess.Popen[bytes] | None = None
        self._last_word = ""
        self._last_started = 0.0
        self._lock = threading.Lock()

    @property
    def available(self) -> bool:
        return self._powershell is not None

    def speak(self, word: str) -> bool:
        """Kimond egy angol szot, es azonnal visszaadja a vezerlest a GUI-nak."""
        clean_word = word.strip()
        if not clean_word or not self._powershell:
            return False
        now = time.monotonic()
        with self._lock:
            if clean_word == self._last_word and now - self._last_started < 0.45:
                return False
            if self._process is not None and self._process.poll() is None:
                self._process.terminate()
            self._last_word = clean_word
            self._last_started = now
            try:
                self._process = subprocess.Popen(
                    self._command_for(clean_word),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError:
                self._process = None
                return False
        return True

    def _command_for(self, word: str) -> list[str]:
        word_data = base64.b64encode(word.encode("utf-8")).decode("ascii")
        script = f"""
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
$englishVoice = $speaker.GetInstalledVoices() | ForEach-Object {{ $_.VoiceInfo }} | Where-Object {{ $_.Culture.Name -like 'en-*' }} | Select-Object -First 1
if ($englishVoice) {{ $speaker.SelectVoice($englishVoice.Name) }}
$speaker.Rate = -1
$word = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{word_data}'))
$speaker.Speak($word)
$speaker.Dispose()
"""
        encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        return [
            self._powershell or "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-WindowStyle",
            "Hidden",
            "-EncodedCommand",
            encoded_script,
        ]