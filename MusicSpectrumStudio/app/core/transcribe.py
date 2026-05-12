"""Lyric extraction pipeline using Groq Whisper + optional AI text correction."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field

from ..constants import GROQ_FALLBACK_LLM
from .ffmpeg_check import resolve_ffmpeg_path
from .groq_client import GroqClient, GroqError

logger = logging.getLogger(__name__)


@dataclass
class WordTiming:
    word: str
    start: float
    end: float


@dataclass
class LyricLine:
    text: str
    start: float
    end: float
    words: list[WordTiming] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    language: str
    duration: float
    lines: list[LyricLine] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "duration": self.duration,
            "lines": [
                {
                    "text": line.text,
                    "start": line.start,
                    "end": line.end,
                    "words": [
                        {"word": w.word, "start": w.start, "end": w.end} for w in line.words
                    ],
                }
                for line in self.lines
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> TranscriptionResult:
        lines = []
        for raw in data.get("lines", []):
            words = [WordTiming(**w) for w in raw.get("words", [])]
            lines.append(LyricLine(raw["text"], raw["start"], raw["end"], words))
        return cls(language=data.get("language", ""), duration=data.get("duration", 0.0), lines=lines)


def _ensure_mp3(audio_path: str, max_mb: float = 24.0) -> tuple[str, bool]:
    """Convert audio to a small mp3 if needed. Return (path, is_temp)."""
    size = os.path.getsize(audio_path)
    ext = os.path.splitext(audio_path)[1].lower()
    if ext == ".mp3" and size <= max_mb * 1024 * 1024:
        return audio_path, False
    try:
        ffmpeg = resolve_ffmpeg_path()
    except Exception as exc:
        logger.warning("ffmpeg tidak tersedia untuk pra-konversi audio: %s", exc)
        return audio_path, False

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    out_path = tmp.name
    bitrate = "96k" if size > 30 * 1024 * 1024 else "128k"
    cmd = [
        ffmpeg, "-y", "-i", audio_path,
        "-vn", "-ac", "1", "-ar", "16000",
        "-codec:a", "libmp3lame", "-b:a", bitrate, out_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return out_path, True
    except subprocess.CalledProcessError as exc:
        logger.warning("Konversi audio ke mp3 gagal: %s", exc.stderr.decode(errors="ignore")[-200:])
        try:
            os.unlink(out_path)
        except OSError:
            pass
        return audio_path, False


def transcribe_audio(
    audio_path: str,
    client: GroqClient,
    *,
    model: str = "whisper-large-v3-turbo",
    language: str = "",
    progress: Callable[[str], None] | None = None,
) -> TranscriptionResult:
    def emit(msg: str) -> None:
        if progress:
            progress(msg)
        logger.info(msg)

    emit(f"Mempersiapkan audio untuk transkripsi ({os.path.basename(audio_path)})...")
    upload_path, is_temp = _ensure_mp3(audio_path)
    try:
        emit(f"Mengirim ke Groq Whisper ({model})...")
        try:
            data = client.transcribe(
                upload_path,
                model=model,
                language=language or None,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
            )
        except GroqError as exc:
            raise GroqError(f"Transkripsi gagal: {exc}") from exc
    finally:
        if is_temp:
            try:
                os.unlink(upload_path)
            except OSError:
                pass

    duration = float(data.get("duration") or 0.0)
    detected_language = str(data.get("language") or "")
    segments = data.get("segments") or []
    words = data.get("words") or []

    lines = _build_lines(segments, words)
    emit(f"Transkripsi selesai: {len(lines)} baris, durasi {duration:.1f}s.")
    return TranscriptionResult(language=detected_language, duration=duration, lines=lines)


def _build_lines(segments: list[dict], words: list[dict]) -> list[LyricLine]:
    lines: list[LyricLine] = []
    if segments:
        for seg in segments:
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            start = float(seg.get("start") or 0.0)
            end = float(seg.get("end") or start)
            seg_words: list[WordTiming] = []
            for w in words:
                ws = float(w.get("start") or 0.0)
                we = float(w.get("end") or ws)
                if ws >= start - 0.05 and we <= end + 0.05:
                    seg_words.append(WordTiming(str(w.get("word") or "").strip(), ws, we))
            lines.append(LyricLine(text=text, start=start, end=end, words=seg_words))
        return lines

    # Fallback: build lines from words by grouping (~7 words per line)
    if words:
        buffer: list[WordTiming] = []
        for w in words:
            buffer.append(
                WordTiming(
                    str(w.get("word") or "").strip(),
                    float(w.get("start") or 0.0),
                    float(w.get("end") or 0.0),
                )
            )
            if len(buffer) >= 7:
                lines.append(_combine(buffer))
                buffer = []
        if buffer:
            lines.append(_combine(buffer))
    return lines


def _combine(words: list[WordTiming]) -> LyricLine:
    text = " ".join(w.word for w in words).strip()
    return LyricLine(text=text, start=words[0].start, end=words[-1].end, words=words)


def ai_correct_lyrics(
    transcription: TranscriptionResult,
    client: GroqClient,
    *,
    model: str = "llama-3.3-70b-versatile",
    progress: Callable[[str], None] | None = None,
) -> TranscriptionResult:
    """Use a Groq LLM to fix awkward transcription mistakes while preserving line/word counts."""

    def emit(msg: str) -> None:
        if progress:
            progress(msg)
        logger.info(msg)

    if not transcription.lines:
        return transcription

    payload = [
        {"index": i, "text": line.text} for i, line in enumerate(transcription.lines)
    ]
    system_prompt = (
        "You are a careful lyric editor. You will receive an array of automatic-speech "
        "recognition transcript lines. Fix obvious mis-hearings, typos, and missing words "
        "while preserving the original meaning, language, and approximate length of each "
        "line. Do NOT translate. Do NOT merge or split lines. Return JSON with the same "
        "schema {\"lines\":[{\"index\":n,\"text\":\"...\"}]} and keep indexes 1:1."
    )
    user_msg = json.dumps({"lines": payload}, ensure_ascii=False)

    models_to_try = [model, GROQ_FALLBACK_LLM]
    last_error: Exception | None = None
    for m in models_to_try:
        try:
            emit(f"Memperbaiki lirik dengan model {m}...")
            resp = client.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                model=m,
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            content = resp["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            mapping = {item["index"]: item["text"] for item in parsed.get("lines", []) if "index" in item}
            for i, line in enumerate(transcription.lines):
                new_text = mapping.get(i)
                if not new_text:
                    continue
                line.text = new_text.strip()
                # Re-distribute word timings proportionally for the new text
                _retime_words(line, new_text.strip())
            emit("Perbaikan lirik selesai.")
            return transcription
        except (GroqError, KeyError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            logger.warning("AI correction gagal dengan %s: %s", m, exc)
            continue
    emit(f"Lewati perbaikan AI: {last_error}")
    return transcription


def _retime_words(line: LyricLine, new_text: str) -> None:
    tokens = [t for t in re.split(r"\s+", new_text) if t]
    if not tokens:
        return
    duration = max(line.end - line.start, 0.01)
    new_words: list[WordTiming] = []
    if line.words and len(line.words) == len(tokens):
        for w, t in zip(line.words, tokens, strict=False):
            new_words.append(WordTiming(t, w.start, w.end))
    else:
        step = duration / len(tokens)
        for i, t in enumerate(tokens):
            s = line.start + step * i
            e = line.start + step * (i + 1)
            new_words.append(WordTiming(t, s, e))
    line.words = new_words
