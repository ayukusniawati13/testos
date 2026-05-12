"""Background worker that runs Groq transcription + AI correction."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from ..core.groq_client import GroqClient
from ..core.transcribe import ai_correct_lyrics, transcribe_audio

logger = logging.getLogger(__name__)


class TranscribeWorker(QThread):
    progressed = Signal(str)
    finished_with_result = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        client: GroqClient,
        audio_path: str,
        *,
        model: str = "whisper-large-v3-turbo",
        language: str = "",
        ai_correct: bool = True,
        correct_model: str = "llama-3.3-70b-versatile",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.client = client
        self.audio_path = audio_path
        self.model = model
        self.language = language
        self.ai_correct = ai_correct
        self.correct_model = correct_model

    def run(self) -> None:
        try:
            tr = transcribe_audio(
                self.audio_path,
                self.client,
                model=self.model,
                language=self.language,
                progress=self.progressed.emit,
            )
            if self.ai_correct and tr.lines:
                tr = ai_correct_lyrics(
                    tr,
                    self.client,
                    model=self.correct_model,
                    progress=self.progressed.emit,
                )
            self.finished_with_result.emit(tr)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Transkripsi gagal: %s", exc)
            self.failed.emit(str(exc))
