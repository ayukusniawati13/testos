"""Audio analysis using librosa for spectrum data extraction."""

import numpy as np
import librosa


class AudioAnalyzer:
    def __init__(self, filepath: str, n_fft: int = 2048, hop_length: int = 512):
        self.filepath = filepath
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.y: np.ndarray | None = None
        self.sr: int = 22050
        self.duration: float = 0.0
        self.spectrum_data: np.ndarray | None = None
        self.times: np.ndarray | None = None

    def load(self) -> None:
        self.y, self.sr = librosa.load(self.filepath, sr=self.sr, mono=True)
        self.duration = librosa.get_duration(y=self.y, sr=self.sr)

    def analyze(self) -> None:
        if self.y is None:
            self.load()
        stft = np.abs(librosa.stft(self.y, n_fft=self.n_fft, hop_length=self.hop_length))
        self.spectrum_data = librosa.amplitude_to_db(stft, ref=np.max)
        n_frames = self.spectrum_data.shape[1]
        self.times = np.linspace(0, self.duration, n_frames)

    def get_spectrum_at_time(self, t: float, n_bands: int = 64) -> np.ndarray:
        if self.spectrum_data is None or self.times is None:
            return np.zeros(n_bands)
        idx = int(np.searchsorted(self.times, t))
        idx = min(idx, self.spectrum_data.shape[1] - 1)
        full = self.spectrum_data[:, idx]
        bands = np.array_split(full, n_bands)
        result = np.array([np.mean(b) for b in bands])
        result = (result + 80) / 80.0
        result = np.clip(result, 0, 1)
        return result

    def get_rms_at_time(self, t: float) -> float:
        if self.y is None:
            return 0.0
        sample_idx = int(t * self.sr)
        window = self.sr // 10
        start = max(0, sample_idx - window // 2)
        end = min(len(self.y), sample_idx + window // 2)
        if start >= end:
            return 0.0
        segment = self.y[start:end]
        return float(np.sqrt(np.mean(segment ** 2)))

    def get_beat_strength_at_time(self, t: float) -> float:
        rms = self.get_rms_at_time(t)
        return min(1.0, rms * 5.0)
