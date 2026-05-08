"""Audio analysis: metadata, time-aligned spectrum frames, beat detection.

This module wraps :mod:`librosa` (and falls back gracefully when it isn't
installed at import time, so the GUI remains importable for tests). The main
entry points are:

* :func:`probe_audio_metadata` -- fast, no heavy decoding.
* :class:`AudioAnalyzer` -- full STFT pipeline producing per-frame
  band energies (overall / bass / mid / treble) and beat times.
"""
from __future__ import annotations

import math
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.utils import validators
from app.utils.logger import get_logger

logger = get_logger("audio_analyzer")


@dataclass
class AudioMetadata:
    path: Path
    duration: float
    sample_rate: int
    channels: int
    bitrate: Optional[int] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "bitrate": self.bitrate,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
        }


@dataclass
class SpectrumFrames:
    """Per-frame analysis result.

    ``magnitudes`` is shaped (n_frames, n_bands) and normalised in [0, 1].
    Each accompanying array is shaped (n_frames,) and normalised in [0, 1].
    Beat times are absolute seconds.
    """

    fps: float
    n_bands: int
    magnitudes: List[List[float]] = field(default_factory=list)
    energy: List[float] = field(default_factory=list)
    bass: List[float] = field(default_factory=list)
    mid: List[float] = field(default_factory=list)
    treble: List[float] = field(default_factory=list)
    beat_times: List[float] = field(default_factory=list)
    duration: float = 0.0

    @property
    def n_frames(self) -> int:
        return len(self.magnitudes)


def probe_audio_metadata(path: Path | str) -> AudioMetadata:
    """Read metadata + duration without loading the entire file when possible."""
    p = validators.ensure_audio(path)

    duration: float = 0.0
    sample_rate = 0
    channels = 0
    bitrate: Optional[int] = None
    title = artist = album = None

    # Try mutagen for metadata + bitrate.
    try:  # pragma: no cover - depends on optional dep
        from mutagen import File as MutagenFile  # type: ignore

        mf = MutagenFile(p)
        if mf is not None:
            info = getattr(mf, "info", None)
            if info is not None:
                duration = float(getattr(info, "length", 0.0) or 0.0)
                sample_rate = int(getattr(info, "sample_rate", 0) or 0)
                channels = int(getattr(info, "channels", 0) or 0)
                bitrate = int(getattr(info, "bitrate", 0) or 0) or None
            tags = getattr(mf, "tags", None)
            if tags is not None:
                title = _first_tag(tags, ("TIT2", "title", "\xa9nam"))
                artist = _first_tag(tags, ("TPE1", "artist", "\xa9ART"))
                album = _first_tag(tags, ("TALB", "album", "\xa9alb"))
    except Exception as exc:  # pragma: no cover - tolerant
        logger.debug("mutagen probe failed: %s", exc)

    # Fallback for WAV files when mutagen is unavailable / incomplete.
    if duration == 0.0 and p.suffix.lower() == ".wav":
        try:
            with wave.open(str(p), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate() or 1
                duration = frames / float(rate)
                sample_rate = sample_rate or rate
                channels = channels or wf.getnchannels()
        except wave.Error:  # pragma: no cover
            pass

    if duration == 0.0:
        # Last resort: librosa.get_duration (may decode part of file).
        try:  # pragma: no cover - heavy dep
            import librosa  # type: ignore

            duration = float(librosa.get_duration(path=str(p)))
        except Exception:
            duration = 0.0

    return AudioMetadata(
        path=p,
        duration=duration,
        sample_rate=sample_rate,
        channels=channels,
        bitrate=bitrate,
        title=title,
        artist=artist,
        album=album,
    )


def _first_tag(tags, keys) -> Optional[str]:
    for key in keys:
        value = tags.get(key)
        if value is None:
            continue
        if isinstance(value, list) and value:
            value = value[0]
        if hasattr(value, "text") and value.text:
            return str(value.text[0])
        if value:
            return str(value)
    return None


class AudioAnalyzer:
    """Compute spectrum frames + beat info from an audio file."""

    DEFAULT_BAND_COUNT = 64
    DEFAULT_FPS = 30
    BASS_RANGE_HZ = (20.0, 250.0)
    MID_RANGE_HZ = (250.0, 4000.0)
    TREBLE_RANGE_HZ = (4000.0, 16000.0)

    def __init__(
        self,
        n_bands: int = DEFAULT_BAND_COUNT,
        fps: float = DEFAULT_FPS,
        smoothing: float = 0.5,
    ) -> None:
        self.n_bands = max(8, int(n_bands))
        self.fps = max(1.0, float(fps))
        self.smoothing = max(0.0, min(0.95, float(smoothing)))

    def analyze(self, audio_path: Path | str) -> SpectrumFrames:
        """Run the full analysis pipeline. Heavy deps imported lazily."""
        path = validators.ensure_audio(audio_path)
        try:  # pragma: no cover - heavy dep
            import librosa  # type: ignore
            import numpy as np  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "librosa/numpy are required for spectrum analysis. "
                "Install them via `pip install -r requirements.txt`."
            ) from exc

        logger.info("Loading audio %s", path)
        y, sr = librosa.load(str(path), sr=None, mono=True)
        duration = float(len(y) / sr) if sr else 0.0

        # Frame size aligned to requested fps so each video frame maps to one STFT.
        hop_length = max(1, int(round(sr / self.fps)))
        n_fft = 2048
        stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, window="hann")
        magnitudes = np.abs(stft).astype("float32")  # shape (freq_bins, frames)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

        bands = self._compute_band_matrix(magnitudes, freqs)
        bands = _smooth_columns(bands, self.smoothing)
        bands = _normalise(bands)

        # Aggregate per-frame band energies for reactive elements.
        energy = bands.mean(axis=0)
        bass = self._range_energy(magnitudes, freqs, self.BASS_RANGE_HZ)
        mid = self._range_energy(magnitudes, freqs, self.MID_RANGE_HZ)
        treble = self._range_energy(magnitudes, freqs, self.TREBLE_RANGE_HZ)

        # Beat tracking.
        try:
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length).tolist()
            logger.info("Detected tempo: %.1f BPM (%d beats)", float(tempo), len(beat_times))
        except Exception as exc:  # pragma: no cover - tolerant
            logger.warning("Beat tracking failed: %s", exc)
            beat_times = []

        # Convert to plain lists so the result is JSON-serialisable / pickle-safe.
        return SpectrumFrames(
            fps=self.fps,
            n_bands=self.n_bands,
            magnitudes=bands.T.tolist(),
            energy=energy.tolist(),
            bass=bass.tolist(),
            mid=mid.tolist(),
            treble=treble.tolist(),
            beat_times=beat_times,
            duration=duration,
        )

    # -------------------------------------------------------------- internals

    def _compute_band_matrix(self, magnitudes, freqs):  # pragma: no cover - heavy
        import numpy as np  # type: ignore

        # Logarithmic band edges between 20 Hz and 16 kHz.
        edges = np.logspace(
            math.log10(20.0), math.log10(min(16000.0, freqs[-1] or 16000.0)),
            self.n_bands + 1,
        )
        n_freq, n_frames = magnitudes.shape
        out = np.zeros((self.n_bands, n_frames), dtype="float32")
        for i in range(self.n_bands):
            lo, hi = edges[i], edges[i + 1]
            idx = np.where((freqs >= lo) & (freqs < hi))[0]
            if idx.size == 0:
                continue
            out[i] = magnitudes[idx].mean(axis=0)
        return out

    def _range_energy(self, magnitudes, freqs, hz_range):  # pragma: no cover
        import numpy as np  # type: ignore

        lo, hi = hz_range
        idx = np.where((freqs >= lo) & (freqs < hi))[0]
        if idx.size == 0:
            return np.zeros(magnitudes.shape[1], dtype="float32")
        slice_ = magnitudes[idx].mean(axis=0)
        smoothed = _smooth_columns(slice_[None, :], self.smoothing)[0]
        peak = float(smoothed.max() or 1.0)
        return (smoothed / peak).astype("float32")


def _smooth_columns(matrix, factor: float):  # pragma: no cover - heavy
    import numpy as np  # type: ignore

    if factor <= 0.0:
        return matrix
    arr = np.asarray(matrix, dtype="float32")
    out = arr.copy()
    for i in range(1, out.shape[1]):
        out[:, i] = factor * out[:, i - 1] + (1 - factor) * arr[:, i]
    return out


def _normalise(matrix):  # pragma: no cover - heavy
    import numpy as np  # type: ignore

    arr = np.asarray(matrix, dtype="float32")
    peak = float(arr.max() or 1.0)
    return arr / peak
