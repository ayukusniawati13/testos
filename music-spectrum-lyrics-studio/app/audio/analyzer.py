"""
Audio analysis engine for spectrum visualization and beat detection.
"""
import numpy as np
import logging
import os
import json
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Analyze audio for spectrum data, beats, and frequency bands."""

    def __init__(self, filepath, sample_rate=44100, fft_size=2048, hop_length=512):
        self.filepath = filepath
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.hop_length = hop_length
        self.audio_data = None
        self.duration = 0.0
        self.spectrum_data = None
        self.beat_frames = None
        self.beat_times = None
        self.tempo = 0.0

    def load_audio(self):
        """Load audio file using librosa."""
        import librosa
        logger.info(f"Loading audio: {self.filepath}")
        self.audio_data, self.sample_rate = librosa.load(
            self.filepath, sr=self.sample_rate, mono=True
        )
        self.duration = len(self.audio_data) / self.sample_rate
        logger.info(f"Audio loaded: duration={self.duration:.2f}s, sr={self.sample_rate}")

    def compute_spectrum(self):
        """Compute STFT spectrum data."""
        import librosa
        if self.audio_data is None:
            self.load_audio()

        stft = librosa.stft(
            self.audio_data,
            n_fft=self.fft_size,
            hop_length=self.hop_length
        )
        self.spectrum_data = np.abs(stft)
        magnitude_db = librosa.amplitude_to_db(self.spectrum_data, ref=np.max)
        self.spectrum_db = magnitude_db
        logger.info(f"Spectrum computed: shape={self.spectrum_data.shape}")
        return self.spectrum_data

    def detect_beats(self):
        """Detect beats in the audio."""
        import librosa
        if self.audio_data is None:
            self.load_audio()

        self.tempo, self.beat_frames = librosa.beat.beat_track(
            y=self.audio_data, sr=self.sample_rate, hop_length=self.hop_length
        )
        self.beat_times = librosa.frames_to_time(
            self.beat_frames, sr=self.sample_rate, hop_length=self.hop_length
        )
        if isinstance(self.tempo, np.ndarray):
            self.tempo = float(self.tempo[0])
        logger.info(f"Beat detection: tempo={self.tempo:.1f} BPM, beats={len(self.beat_times)}")
        return self.beat_times

    def get_spectrum_at_time(self, time_sec, bar_count=64, bass_boost=1.0, treble_reaction=1.0, sensitivity=1.0):
        """Get spectrum bars at a specific time."""
        import librosa
        if self.spectrum_data is None:
            self.compute_spectrum()

        frame = int(time_sec * self.sample_rate / self.hop_length)
        frame = min(frame, self.spectrum_data.shape[1] - 1)
        frame = max(frame, 0)

        spectrum = self.spectrum_data[:, frame].copy()
        n_bins = len(spectrum)

        freq_per_bin = self.sample_rate / self.fft_size
        bass_end = int(250 / freq_per_bin)
        mid_end = int(4000 / freq_per_bin)

        spectrum[:bass_end] *= bass_boost
        spectrum[mid_end:] *= treble_reaction
        spectrum *= sensitivity

        if n_bins > bar_count:
            indices = np.linspace(0, n_bins - 1, bar_count + 1, dtype=int)
            bars = np.array([
                np.mean(spectrum[indices[i]:indices[i + 1]])
                for i in range(bar_count)
            ])
        else:
            bars = np.interp(
                np.linspace(0, n_bins - 1, bar_count),
                np.arange(n_bins), spectrum
            )

        max_val = np.max(bars) if np.max(bars) > 0 else 1.0
        bars = bars / max_val
        return bars

    def is_beat_at_time(self, time_sec, tolerance=0.05):
        """Check if there's a beat at the given time."""
        if self.beat_times is None:
            self.detect_beats()
        for bt in self.beat_times:
            if abs(bt - time_sec) < tolerance:
                return True
        return False

    def get_bass_energy(self, time_sec):
        """Get bass energy at a specific time (0-1)."""
        if self.spectrum_data is None:
            self.compute_spectrum()

        frame = int(time_sec * self.sample_rate / self.hop_length)
        frame = min(frame, self.spectrum_data.shape[1] - 1)
        frame = max(frame, 0)

        freq_per_bin = self.sample_rate / self.fft_size
        bass_end = int(250 / freq_per_bin)
        bass_energy = np.mean(self.spectrum_data[:bass_end, frame])
        max_energy = np.max(self.spectrum_data[:bass_end]) if np.max(self.spectrum_data[:bass_end]) > 0 else 1.0
        return float(bass_energy / max_energy)

    def save_cache(self, cache_dir):
        """Save analysis cache."""
        from app.utils.helpers import get_file_hash
        os.makedirs(cache_dir, exist_ok=True)
        file_hash = get_file_hash(self.filepath)
        cache_file = os.path.join(cache_dir, f"{file_hash}_analysis.npz")

        data = {
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "tempo": self.tempo,
        }
        if self.spectrum_data is not None:
            np.savez_compressed(
                cache_file,
                spectrum=self.spectrum_data,
                beat_times=self.beat_times if self.beat_times is not None else np.array([]),
            )
        meta_file = os.path.join(cache_dir, f"{file_hash}_meta.json")
        with open(meta_file, "w") as f:
            json.dump(data, f)

        logger.info(f"Analysis cache saved: {cache_file}")

    def load_cache(self, cache_dir):
        """Load analysis from cache if available."""
        from app.utils.helpers import get_file_hash
        file_hash = get_file_hash(self.filepath)
        cache_file = os.path.join(cache_dir, f"{file_hash}_analysis.npz")
        meta_file = os.path.join(cache_dir, f"{file_hash}_meta.json")

        if os.path.exists(cache_file) and os.path.exists(meta_file):
            try:
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                data = np.load(cache_file)
                self.spectrum_data = data["spectrum"]
                bt = data["beat_times"]
                self.beat_times = bt if len(bt) > 0 else None
                self.duration = meta["duration"]
                self.tempo = meta.get("tempo", 0.0)
                logger.info(f"Analysis loaded from cache: {cache_file}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return False


class AudioAnalysisThread(QThread):
    """Background thread for audio analysis."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, filepath, cache_dir=None):
        super().__init__()
        self.filepath = filepath
        self.cache_dir = cache_dir

    def run(self):
        try:
            analyzer = AudioAnalyzer(self.filepath)

            if self.cache_dir and analyzer.load_cache(self.cache_dir):
                self.progress.emit(100, "Loaded from cache")
                self.finished.emit(analyzer)
                return

            self.progress.emit(10, "Loading audio...")
            analyzer.load_audio()

            self.progress.emit(40, "Computing spectrum...")
            analyzer.compute_spectrum()

            self.progress.emit(70, "Detecting beats...")
            analyzer.detect_beats()

            if self.cache_dir:
                self.progress.emit(90, "Saving cache...")
                analyzer.save_cache(self.cache_dir)

            self.progress.emit(100, "Analysis complete")
            self.finished.emit(analyzer)
        except Exception as e:
            logger.error(f"Audio analysis error: {e}")
            self.error.emit(str(e))
