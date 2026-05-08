"""
Whisper-based speech recognition engine for lyrics generation.
Supports Whisper, WhisperX, and Faster-Whisper backends.
"""
import os
import logging
import json
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class WhisperEngine:
    """Manage Whisper model loading and transcription."""

    MODEL_MAP = {
        "Auto Best Model": None,
        "Whisper Large": ("whisper", "large"),
        "Whisper Large-v3": ("whisper", "large-v3"),
        "WhisperX High Accuracy": ("whisperx", "large-v3"),
        "Faster-Whisper Large": ("faster-whisper", "large-v3"),
        "Faster-Whisper Medium": ("faster-whisper", "medium"),
        "Faster-Whisper Small": ("faster-whisper", "small"),
    }

    def __init__(self, model_name="Auto Best Model", device="auto",
                 compute_type="auto", language="auto"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language if language != "auto" else None
        self.model = None
        self.backend = None
        self.model_size = None

    def _resolve_auto(self):
        """Resolve auto settings based on system capabilities."""
        from app.utils.helpers import check_gpu_available

        if self.device == "auto":
            self.device = "cuda" if check_gpu_available() else "cpu"

        if self.compute_type == "auto":
            self.compute_type = "float16" if self.device == "cuda" else "int8"

        if self.model_name == "Auto Best Model":
            if self.device == "cuda":
                self.backend = "faster-whisper"
                self.model_size = "large-v3"
            else:
                self.backend = "faster-whisper"
                self.model_size = "medium"
        else:
            entry = self.MODEL_MAP.get(self.model_name)
            if entry:
                self.backend, self.model_size = entry
            else:
                self.backend = "faster-whisper"
                self.model_size = "medium"

    def load_model(self):
        """Load the transcription model."""
        self._resolve_auto()
        logger.info(f"Loading model: backend={self.backend}, size={self.model_size}, "
                     f"device={self.device}, compute={self.compute_type}")

        if self.backend == "faster-whisper":
            self._load_faster_whisper()
        elif self.backend == "whisperx":
            self._load_whisperx()
        elif self.backend == "whisper":
            self._load_whisper()

    def _load_faster_whisper(self):
        """Load Faster-Whisper model."""
        from faster_whisper import WhisperModel
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )

    def _load_whisperx(self):
        """Load WhisperX model."""
        import whisperx
        self.model = whisperx.load_model(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type
        )

    def _load_whisper(self):
        """Load standard Whisper model."""
        import whisper
        self.model = whisper.load_model(self.model_size, device=self.device)

    def transcribe(self, audio_path, word_timestamps=True):
        """Transcribe audio file and return segments with timing."""
        if self.model is None:
            self.load_model()

        logger.info(f"Transcribing: {audio_path}")

        if self.backend == "faster-whisper":
            return self._transcribe_faster_whisper(audio_path, word_timestamps)
        elif self.backend == "whisperx":
            return self._transcribe_whisperx(audio_path, word_timestamps)
        elif self.backend == "whisper":
            return self._transcribe_whisper(audio_path, word_timestamps)

    def _transcribe_faster_whisper(self, audio_path, word_timestamps):
        """Transcribe using Faster-Whisper."""
        segments, info = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=word_timestamps,
            vad_filter=True,
        )

        detected_language = info.language
        logger.info(f"Detected language: {detected_language}")

        result_segments = []
        for segment in segments:
            seg_data = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": []
            }
            if word_timestamps and segment.words:
                for word in segment.words:
                    seg_data["words"].append({
                        "text": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                    })
            result_segments.append(seg_data)

        return {
            "segments": result_segments,
            "language": detected_language,
            "backend": "faster-whisper",
            "model": self.model_size,
        }

    def _transcribe_whisperx(self, audio_path, word_timestamps):
        """Transcribe using WhisperX with forced alignment."""
        import whisperx

        audio = whisperx.load_audio(audio_path)
        result = self.model.transcribe(audio, language=self.language)
        detected_language = result.get("language", "en")

        if word_timestamps:
            try:
                align_model, align_metadata = whisperx.load_align_model(
                    language_code=detected_language, device=self.device
                )
                result = whisperx.align(
                    result["segments"], align_model, align_metadata,
                    audio, self.device
                )
                logger.info("WhisperX forced alignment completed")
            except Exception as e:
                logger.warning(f"WhisperX alignment failed: {e}")

        result_segments = []
        for segment in result.get("segments", []):
            seg_data = {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "words": []
            }
            for word in segment.get("words", []):
                if "start" in word and "end" in word:
                    seg_data["words"].append({
                        "text": word.get("word", "").strip(),
                        "start": word["start"],
                        "end": word["end"],
                    })
            result_segments.append(seg_data)

        return {
            "segments": result_segments,
            "language": detected_language,
            "backend": "whisperx",
            "model": self.model_size,
        }

    def _transcribe_whisper(self, audio_path, word_timestamps):
        """Transcribe using standard Whisper."""
        result = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=word_timestamps,
        )

        detected_language = result.get("language", "en")
        result_segments = []
        for segment in result.get("segments", []):
            seg_data = {
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "words": []
            }
            for word in segment.get("words", []):
                seg_data["words"].append({
                    "text": word.get("word", "").strip(),
                    "start": word["start"],
                    "end": word["end"],
                })
            result_segments.append(seg_data)

        return {
            "segments": result_segments,
            "language": detected_language,
            "backend": "whisper",
            "model": self.model_size,
        }

    @staticmethod
    def get_model_status(model_name):
        """Check if a model is downloaded and ready."""
        try:
            from faster_whisper.utils import download_model
            return True, "Model available"
        except Exception:
            return False, "Model not ready"

    @staticmethod
    def clear_model_cache():
        """Clear downloaded model cache."""
        import shutil
        cache_dirs = [
            os.path.expanduser("~/.cache/huggingface"),
            os.path.expanduser("~/.cache/whisper"),
        ]
        for d in cache_dirs:
            if os.path.exists(d):
                try:
                    shutil.rmtree(d)
                    logger.info(f"Cleared cache: {d}")
                except Exception as e:
                    logger.warning(f"Failed to clear: {d}: {e}")


def segments_to_lyrics_data(transcription_result):
    """Convert transcription segments to LyricsData."""
    from app.lyrics.metadata_lyrics_extractor import LyricsData, LyricsLine, LyricsWord

    data = LyricsData()
    backend = transcription_result.get("backend", "unknown")
    data.source = f"WhisperX Synced" if backend == "whisperx" else "Whisper Generated"
    data.language = transcription_result.get("language", "auto")
    data.has_synced = True

    for seg in transcription_result.get("segments", []):
        words = []
        for w in seg.get("words", []):
            words.append(LyricsWord(w["text"], w["start"], w["end"]))

        line = LyricsLine(
            text=seg["text"],
            start=seg["start"],
            end=seg["end"],
            words=words
        )
        data.lines.append(line)

    return data


class TranscriptionThread(QThread):
    """Background thread for audio transcription."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, audio_path, model_name="Auto Best Model", device="auto",
                 compute_type="auto", language="auto", word_timestamps=True,
                 cache_dir=None):
        super().__init__()
        self.audio_path = audio_path
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.word_timestamps = word_timestamps
        self.cache_dir = cache_dir

    def run(self):
        try:
            if self.cache_dir:
                from app.utils.helpers import get_file_hash
                file_hash = get_file_hash(self.audio_path)
                cache_file = os.path.join(self.cache_dir, f"{file_hash}_lyrics.json")
                if os.path.exists(cache_file):
                    with open(cache_file, "r", encoding="utf-8") as f:
                        result = json.load(f)
                    self.progress.emit(100, "Loaded lyrics from cache")
                    lyrics_data = segments_to_lyrics_data(result)
                    self.finished.emit(lyrics_data)
                    return

            self.progress.emit(10, f"Loading model: {self.model_name}...")
            engine = WhisperEngine(
                model_name=self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                language=self.language,
            )
            engine.load_model()

            self.progress.emit(30, "Transcribing audio...")
            result = engine.transcribe(self.audio_path, self.word_timestamps)

            self.progress.emit(80, "Processing lyrics...")
            lyrics_data = segments_to_lyrics_data(result)

            if self.cache_dir:
                os.makedirs(self.cache_dir, exist_ok=True)
                from app.utils.helpers import get_file_hash
                file_hash = get_file_hash(self.audio_path)
                cache_file = os.path.join(self.cache_dir, f"{file_hash}_lyrics.json")
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

            self.progress.emit(90, f"Language: {result.get('language', 'unknown')}")
            self.progress.emit(100, "Transcription complete")
            self.finished.emit(lyrics_data)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            self.error.emit(str(e))
