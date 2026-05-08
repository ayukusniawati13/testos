"""Lyric handling: Whisper transcription + SRT/LRC/TXT IO + display planning.

The :class:`LyricEngine` exposes everything the GUI needs:

* :meth:`transcribe` -- run faster-whisper (optionally refined by stable-ts)
  to get word-level lyric segments.
* :meth:`load` / :meth:`save` -- import / export lyrics in any of the
  supported text formats.
* :meth:`render_frame` -- draw the appropriate text onto an RGBA layer for a
  given playback time.
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from app.utils import file_utils, validators
from app.utils.logger import get_logger

logger = get_logger("lyric_engine")


SUPPORTED_DISPLAY_MODES: Tuple[str, ...] = ("line", "karaoke", "highlight", "fade")


@dataclass
class LyricWord:
    text: str
    start: float
    end: float


@dataclass
class LyricLine:
    text: str
    start: float
    end: float
    words: List[LyricWord] = field(default_factory=list)

    def has_word_timing(self) -> bool:
        return bool(self.words) and any(w.end > w.start for w in self.words)


@dataclass
class LyricTrack:
    lines: List[LyricLine] = field(default_factory=list)
    language: Optional[str] = None
    source: str = "unknown"  # whisper / srt / lrc / txt / manual

    def to_plain_text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    def is_empty(self) -> bool:
        return not self.lines


@dataclass
class LyricStyle:
    """Visual configuration for the lyric overlay."""

    enabled: bool = True
    display_mode: str = "highlight"
    font_family: str = "Inter"
    font_size: int = 56
    font_color: str = "#ffffff"
    highlight_color: str = "#21d4fd"
    outline_color: str = "#000000"
    y_position: float = 0.7
    fade_seconds: float = 0.25
    line_width_ratio: float = 0.85

    @classmethod
    def from_dict(cls, data: dict) -> "LyricStyle":
        return cls(
            enabled=bool(data.get("enabled", True)),
            display_mode=str(data.get("display_mode", "highlight")),
            font_family=str(data.get("font_family", "Inter")),
            font_size=int(data.get("font_size", 56)),
            font_color=str(data.get("font_color", "#ffffff")),
            highlight_color=str(data.get("highlight_color", "#21d4fd")),
            outline_color=str(data.get("outline_color", "#000000")),
            y_position=float(data.get("y_position", 0.7)),
            fade_seconds=float(data.get("fade_seconds", 0.25)),
            line_width_ratio=float(data.get("line_width_ratio", 0.85)),
        )


# ---------------------------------------------------------------------- engine


class LyricEngine:
    """Transcription + persistence + per-frame rendering."""

    def __init__(self, style: LyricStyle, model: str = "base", language: str = "auto") -> None:
        self.style = style
        self.model = model
        self.language = language
        self._track: LyricTrack = LyricTrack()
        self._font_cache: dict = {}

    # ------------------------------------------------------------ transcription

    def transcribe(
        self,
        audio_path: Path | str,
        progress_cb: Optional[callable] = None,
    ) -> LyricTrack:
        """Run faster-whisper on ``audio_path`` and return a :class:`LyricTrack`."""
        path = validators.ensure_audio(audio_path)
        try:  # pragma: no cover - heavy dep
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        logger.info("Loading Whisper model %s", self.model)
        compute_type = "int8" if self.model in ("tiny", "base", "small") else "int8_float32"
        whisper = WhisperModel(self.model, compute_type=compute_type)
        language = None if self.language in ("", "auto", None) else self.language

        logger.info("Transcribing %s", path)
        segments, info = whisper.transcribe(
            str(path),
            language=language,
            word_timestamps=True,
            vad_filter=True,
        )

        lines: List[LyricLine] = []
        # Whisper streams segments — iterate and emit progress updates.
        total_duration = float(getattr(info, "duration", 0.0) or 0.0) or None
        for seg in segments:
            words: List[LyricWord] = []
            for w in (seg.words or []):
                if w.word is None:
                    continue
                token = str(w.word).strip()
                if not token:
                    continue
                words.append(
                    LyricWord(text=token, start=float(w.start or seg.start), end=float(w.end or seg.end))
                )
            text = (seg.text or "").strip()
            if not text:
                continue
            lines.append(
                LyricLine(text=text, start=float(seg.start or 0.0), end=float(seg.end or 0.0), words=words)
            )
            if progress_cb and total_duration:
                progress_cb(min(1.0, float(seg.end or 0.0) / total_duration))

        track = LyricTrack(lines=lines, language=str(getattr(info, "language", "")) or None, source="whisper")
        track = self._maybe_align_with_stable_ts(path, track)
        self._track = track
        logger.info("Transcribed %d line(s)", len(lines))
        return track

    def _maybe_align_with_stable_ts(self, audio_path: Path, track: LyricTrack) -> LyricTrack:
        """Optionally refine timings with stable-ts (best-effort)."""
        try:  # pragma: no cover - optional dep
            import stable_whisper  # type: ignore
        except ImportError:
            return track

        try:
            model = stable_whisper.load_faster_whisper(self.model)
            result = model.transcribe(str(audio_path), language=self.language or None, word_timestamps=True)
            refined: List[LyricLine] = []
            for seg in getattr(result, "segments", []):
                words: List[LyricWord] = []
                for w in getattr(seg, "words", []) or []:
                    text = str(getattr(w, "word", "") or "").strip()
                    if not text:
                        continue
                    words.append(
                        LyricWord(text=text, start=float(w.start), end=float(w.end))
                    )
                line_text = str(getattr(seg, "text", "") or "").strip()
                if not line_text:
                    continue
                refined.append(
                    LyricLine(
                        text=line_text,
                        start=float(getattr(seg, "start", 0.0)),
                        end=float(getattr(seg, "end", 0.0)),
                        words=words,
                    )
                )
            if refined:
                logger.info("Refined %d line(s) via stable-ts", len(refined))
                return LyricTrack(lines=refined, language=track.language, source="stable_ts")
        except Exception as exc:  # pragma: no cover - tolerant
            logger.warning("stable-ts refinement failed: %s", exc)
        return track

    # --------------------------------------------------------------- access

    @property
    def track(self) -> LyricTrack:
        return self._track

    def set_track(self, track: LyricTrack) -> None:
        self._track = track

    # --------------------------------------------------------------- IO

    def load(self, path: Path | str) -> LyricTrack:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(p)
        suffix = p.suffix.lower()
        if suffix == ".srt":
            track = parse_srt(p.read_text(encoding="utf-8", errors="replace"))
        elif suffix == ".lrc":
            track = parse_lrc(p.read_text(encoding="utf-8", errors="replace"))
        elif suffix == ".txt":
            track = parse_txt(p.read_text(encoding="utf-8", errors="replace"))
        else:
            raise ValueError(f"Unsupported lyric format '{suffix}'.")
        track.source = suffix.lstrip(".")
        self._track = track
        return track

    def save(self, path: Path | str, fmt: str | None = None) -> Path:
        p = Path(path)
        fmt = (fmt or p.suffix.lstrip(".") or "srt").lower()
        text: str
        if fmt == "srt":
            text = serialize_srt(self._track)
        elif fmt == "lrc":
            text = serialize_lrc(self._track)
        elif fmt == "txt":
            text = self._track.to_plain_text()
        else:
            raise ValueError(f"Unsupported lyric format '{fmt}'.")
        file_utils.ensure_dir(p.parent)
        p.write_text(text, encoding="utf-8")
        return p

    # --------------------------------------------------------------- rendering

    def render_frame(self, size: Tuple[int, int], time: float) -> Optional[Image.Image]:
        """Return an RGBA image with the lyric overlay for ``time`` (seconds)."""
        if not self.style.enabled or self._track.is_empty():
            return None

        line = _line_at(self._track.lines, time)
        if line is None:
            return None

        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas, "RGBA")
        font = self._load_font(self.style.font_size)
        outline = _hex(self.style.outline_color)
        body_color = _hex(self.style.font_color)
        highlight = _hex(self.style.highlight_color)

        text = line.text.strip()
        if not text:
            return None

        max_text_width = int(size[0] * self.style.line_width_ratio)
        wrapped_lines = _wrap_text(draw, text, font, max_text_width)
        line_heights = [_text_size(draw, t, font)[1] for t in wrapped_lines]
        block_height = sum(line_heights) + (len(wrapped_lines) - 1) * 8

        y_anchor = int(size[1] * self.style.y_position - block_height / 2)

        alpha = _line_alpha(line, time, self.style.fade_seconds)
        if alpha <= 0:
            return None

        for idx, t in enumerate(wrapped_lines):
            line_w, line_h = _text_size(draw, t, font)
            x_anchor = int((size[0] - line_w) / 2)

            mode = self.style.display_mode
            if mode == "karaoke" and line.has_word_timing():
                _draw_karaoke(draw, line, t, font, x_anchor, y_anchor, body_color, highlight, outline, time, alpha)
            elif mode == "highlight" and line.has_word_timing():
                _draw_highlighted(draw, line, t, font, x_anchor, y_anchor, body_color, highlight, outline, time, alpha)
            elif mode == "fade":
                _draw_simple(draw, t, font, x_anchor, y_anchor, body_color, outline, alpha)
            else:  # plain "line"
                _draw_simple(draw, t, font, x_anchor, y_anchor, body_color, outline, alpha)
            y_anchor += line_h + 8
        return canvas

    def _load_font(self, size: int) -> ImageFont.ImageFont:
        cache_key = (self.style.font_family, size)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        font: ImageFont.ImageFont
        candidates = [
            self.style.font_family,
            "Inter-Regular.ttf",
            "DejaVuSans.ttf",
            "Arial.ttf",
        ]
        for name in candidates:
            try:
                font = ImageFont.truetype(name, size=size)
                break
            except (OSError, IOError):
                continue
        else:
            font = ImageFont.load_default()
        self._font_cache[cache_key] = font
        return font


# --------------------------------------------------------------- helpers / IO


def _line_at(lines: Sequence[LyricLine], time: float) -> Optional[LyricLine]:
    for line in lines:
        if line.start <= time < line.end:
            return line
    # Show last line briefly after song ends.
    if lines and time >= lines[-1].end and time - lines[-1].end < 1.0:
        return lines[-1]
    return None


def _line_alpha(line: LyricLine, time: float, fade: float) -> float:
    if fade <= 0:
        return 1.0
    if time < line.start + fade:
        return max(0.0, (time - line.start) / fade)
    if time > line.end - fade:
        return max(0.0, 1.0 - (time - (line.end - fade)) / fade)
    return 1.0


def _hex(value: str):
    s = value.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4)) + (255,)


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        candidate = (" ".join(current + [word])).strip()
        w, _ = _text_size(draw, candidate, font)
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines or [text]


def _draw_simple(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    color,
    outline,
    alpha: float,
) -> None:
    fill = color[:3] + (int(color[3] * alpha),)
    out = outline[:3] + (int(outline[3] * alpha),)
    draw.text((x, y), text, font=font, fill=fill, stroke_width=2, stroke_fill=out)


def _draw_highlighted(
    draw: ImageDraw.ImageDraw,
    line: LyricLine,
    rendered_text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    body_color,
    highlight,
    outline,
    time: float,
    alpha: float,
) -> None:
    """Draw the line and recolour the currently-spoken word."""
    cursor_x = x
    word_index = _active_word_index(line, time)
    word_index_local = 0
    for token in rendered_text.split(" "):
        is_active = word_index == word_index_local
        color = highlight if is_active else body_color
        _draw_simple(draw, token, font, cursor_x, y, color, outline, alpha)
        token_w, _ = _text_size(draw, token + " ", font)
        cursor_x += token_w
        word_index_local += 1


def _draw_karaoke(
    draw: ImageDraw.ImageDraw,
    line: LyricLine,
    rendered_text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    body_color,
    highlight,
    outline,
    time: float,
    alpha: float,
) -> None:
    """Draw the line twice: a base text + a moving highlight overlay."""
    _draw_simple(draw, rendered_text, font, x, y, body_color, outline, alpha)
    if not line.has_word_timing():
        return
    progress = _karaoke_progress(line, time)
    full_w, full_h = _text_size(draw, rendered_text, font)
    fill_w = int(full_w * progress)
    if fill_w <= 0:
        return
    mask = Image.new("L", (fill_w, full_h + 8), 255)
    overlay = Image.new("RGBA", (fill_w, full_h + 8), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay, "RGBA")
    color = highlight[:3] + (int(highlight[3] * alpha),)
    overlay_draw.text((0, 0), rendered_text, font=font, fill=color)
    base = draw._image  # type: ignore[attr-defined]
    base.paste(overlay, (x, y), mask)


def _active_word_index(line: LyricLine, time: float) -> int:
    if not line.words:
        return -1
    for idx, w in enumerate(line.words):
        if w.start <= time < w.end:
            return idx
    if time < line.words[0].start:
        return -1
    return len(line.words) - 1


def _karaoke_progress(line: LyricLine, time: float) -> float:
    if not line.has_word_timing():
        if line.end <= line.start:
            return 0.0
        return max(0.0, min(1.0, (time - line.start) / (line.end - line.start)))
    total = sum(max(0.0, w.end - w.start) for w in line.words) or 1e-6
    elapsed = 0.0
    for w in line.words:
        dur = max(0.0, w.end - w.start)
        if time < w.start:
            return elapsed / total
        if time < w.end:
            return (elapsed + (time - w.start)) / total
        elapsed += dur
    return 1.0


# --------------------------------------------------------------- format IO


_TIMESTAMP_SRT_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2})[\.,](\d{1,3})")
_TIMESTAMP_LRC_RE = re.compile(r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]")


def parse_srt(text: str) -> LyricTrack:
    blocks = re.split(r"\n\s*\n", text.strip(), flags=re.MULTILINE)
    lines: List[LyricLine] = []
    for block in blocks:
        if not block.strip():
            continue
        rows = block.strip().splitlines()
        if len(rows) < 2:
            continue
        timing = rows[1] if "-->" in rows[1] else rows[0]
        match = _TIMESTAMP_SRT_RE.findall(timing)
        if len(match) < 2:
            continue
        start = _to_seconds(*match[0])
        end = _to_seconds(*match[1])
        body = " ".join(rows[2:]) if "-->" in rows[1] else " ".join(rows[1:])
        body = body.strip()
        if body:
            lines.append(LyricLine(text=body, start=start, end=end))
    return LyricTrack(lines=lines, source="srt")


def serialize_srt(track: LyricTrack) -> str:
    out: List[str] = []
    for idx, line in enumerate(track.lines, start=1):
        out.append(str(idx))
        out.append(f"{_format_srt(line.start)} --> {_format_srt(line.end)}")
        out.append(line.text)
        out.append("")
    return "\n".join(out)


def parse_lrc(text: str) -> LyricTrack:
    lines: List[LyricLine] = []
    pending: List[Tuple[float, str]] = []
    for raw in text.splitlines():
        timestamps = _TIMESTAMP_LRC_RE.findall(raw)
        body = _TIMESTAMP_LRC_RE.sub("", raw).strip()
        if not timestamps:
            continue
        for h_min, sec, frac in timestamps:
            seconds = int(h_min) * 60 + int(sec) + (int((frac or "0").ljust(3, "0")[:3]) / 1000.0)
            pending.append((seconds, body))
    pending.sort(key=lambda t: t[0])
    for i, (start, body) in enumerate(pending):
        end = pending[i + 1][0] if i + 1 < len(pending) else start + 3.0
        if body:
            lines.append(LyricLine(text=body, start=start, end=end))
    return LyricTrack(lines=lines, source="lrc")


def serialize_lrc(track: LyricTrack) -> str:
    out: List[str] = []
    for line in track.lines:
        ts = _format_lrc(line.start)
        out.append(f"{ts}{line.text}")
    return "\n".join(out)


def parse_txt(text: str) -> LyricTrack:
    """Plain text -> equally-spaced lyric lines as a fallback."""
    rows = [r.strip() for r in text.splitlines() if r.strip()]
    if not rows:
        return LyricTrack(lines=[], source="txt")
    duration_per_line = 4.0
    lines = [
        LyricLine(text=row, start=i * duration_per_line, end=(i + 1) * duration_per_line)
        for i, row in enumerate(rows)
    ]
    return LyricTrack(lines=lines, source="txt")


def _to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000.0


def _format_srt(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - math.floor(seconds)) * 1000)) % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_lrc(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    m = int(seconds // 60)
    s = seconds - m * 60
    return f"[{m:02d}:{s:05.2f}]"
