"""Audio loading + FFT/spectrum analysis used to drive the visualizer."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AudioData:
    samples: np.ndarray  # mono float32 in [-1, 1]
    sample_rate: int
    duration: float


def load_audio(path: str, target_sr: int = 22050) -> AudioData:
    """Return mono audio. Uses soundfile (+ librosa for resampling) when available."""
    import soundfile as sf

    samples, sr = sf.read(path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if sr != target_sr:
        try:
            import librosa

            samples = librosa.resample(samples, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        except Exception as exc:  # pragma: no cover
            logger.warning("Resample fallback (rate %s); librosa unavailable: %s", sr, exc)
    duration = len(samples) / float(sr)
    return AudioData(samples=samples.astype(np.float32, copy=False), sample_rate=sr, duration=duration)


def _log_band_indices(num_bands: int, fft_size: int, sample_rate: int, fmin: float = 30.0, fmax: float = 16000.0) -> np.ndarray:
    fmax = min(fmax, sample_rate / 2.0)
    edges = np.logspace(np.log10(fmin), np.log10(fmax), num_bands + 1)
    # convert to bin indices
    freqs = np.linspace(0, sample_rate / 2.0, fft_size // 2 + 1)
    return np.searchsorted(freqs, edges).clip(0, len(freqs) - 1)


@dataclass
class SpectrumStream:
    """Pre-computed per-frame spectrum + loudness arrays.

    Shape:
      bands: (frames, num_bands)  -> values in [0, 1]
      loudness: (frames,)         -> RMS in [0, 1]
      beat: (frames,)             -> 0/1 beat marker (sparse)
    """

    bands: np.ndarray
    loudness: np.ndarray
    beat: np.ndarray
    fps: int
    num_bands: int


def analyze_audio(
    audio: AudioData,
    *,
    fps: int = 30,
    num_bands: int = 64,
    fft_size: int = 2048,
    smoothing: float = 0.6,
) -> SpectrumStream:
    """Compute per-frame log-spaced spectrum bands."""
    samples = audio.samples
    sr = audio.sample_rate
    hop = max(1, int(sr / fps))
    n_frames = max(1, int(np.ceil(len(samples) / hop)))
    # Pad samples so we always have a full window
    pad = fft_size
    padded = np.concatenate([np.zeros(pad // 2, dtype=np.float32), samples, np.zeros(pad, dtype=np.float32)])
    window = np.hanning(fft_size).astype(np.float32)

    band_edges = _log_band_indices(num_bands, fft_size, sr)
    bands = np.zeros((n_frames, num_bands), dtype=np.float32)
    loudness = np.zeros(n_frames, dtype=np.float32)

    for i in range(n_frames):
        start = i * hop
        seg = padded[start : start + fft_size]
        if len(seg) < fft_size:
            seg = np.pad(seg, (0, fft_size - len(seg)))
        spec = np.fft.rfft(seg * window)
        mag = np.abs(spec).astype(np.float32)
        for b in range(num_bands):
            lo = band_edges[b]
            hi = max(band_edges[b + 1], lo + 1)
            bands[i, b] = mag[lo:hi].mean() if hi > lo else 0.0
        loudness[i] = float(np.sqrt(np.mean(seg ** 2)))

    # Convert to dB-ish and normalise
    bands = np.log1p(bands * 8.0)
    if bands.max() > 0:
        bands = bands / bands.max()
    # boost mids slightly
    band_axis = np.linspace(0, 1, num_bands)
    boost = 1.0 + 0.4 * np.exp(-((band_axis - 0.5) ** 2) / 0.08)
    bands = np.clip(bands * boost, 0.0, 1.0)

    # temporal smoothing for nicer motion
    if smoothing > 0:
        a = float(smoothing)
        smoothed = np.empty_like(bands)
        smoothed[0] = bands[0]
        for i in range(1, n_frames):
            smoothed[i] = a * smoothed[i - 1] + (1 - a) * bands[i]
        # Allow downward attack to feel snappy
        attack = np.maximum(smoothed, bands * 0.85 + smoothed * 0.15)
        bands = attack

    # loudness 0..1
    if loudness.max() > 0:
        loudness = loudness / loudness.max()
    loudness = np.clip(loudness, 0.0, 1.0)

    beat = _detect_beats(audio, n_frames, fps)
    return SpectrumStream(bands=bands, loudness=loudness, beat=beat, fps=fps, num_bands=num_bands)


def _detect_beats(audio: AudioData, n_frames: int, fps: int) -> np.ndarray:
    beats = np.zeros(n_frames, dtype=np.float32)
    try:
        import librosa

        onset_env = librosa.onset.onset_strength(y=audio.samples, sr=audio.sample_rate)
        tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=audio.sample_rate)
        beat_times = librosa.frames_to_time(beat_frames, sr=audio.sample_rate)
        for t in beat_times:
            idx = int(round(t * fps))
            if 0 <= idx < n_frames:
                beats[idx] = 1.0
    except Exception as exc:  # pragma: no cover
        logger.debug("librosa beat detection unavailable: %s", exc)
    return beats
