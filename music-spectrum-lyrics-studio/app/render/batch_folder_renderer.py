"""
Batch folder renderer - process multiple audio files with automatic lyrics and backgrounds.
"""
import os
import random
import logging
import csv
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

from app.core.config import SUPPORTED_AUDIO, SUPPORTED_IMAGE_BG, SUPPORTED_VIDEO_BG, DIRS
from app.utils.helpers import safe_filename

logger = logging.getLogger(__name__)


class BatchFolderRenderer:
    """Manage batch rendering from folder of audio files."""

    def __init__(self):
        self.audio_folder = ""
        self.background_folder = ""
        self.output_folder = DIRS["output"]
        self.bg_mode = "Random Background"
        self.render_settings = {}
        self.auto_lyrics = True
        self.auto_sync = True
        self.use_metadata = True
        self.logo_enabled = False
        self.cta_enabled = False
        self._jobs = []

    def scan_audio_files(self):
        """Scan audio folder for supported files."""
        files = []
        if not os.path.isdir(self.audio_folder):
            return files
        for fname in sorted(os.listdir(self.audio_folder)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in SUPPORTED_AUDIO:
                files.append(os.path.join(self.audio_folder, fname))
        return files

    def scan_background_files(self):
        """Scan background folder for supported files."""
        files = []
        if not os.path.isdir(self.background_folder):
            return files
        supported = SUPPORTED_IMAGE_BG + SUPPORTED_VIDEO_BG
        for fname in sorted(os.listdir(self.background_folder)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in supported:
                files.append(os.path.join(self.background_folder, fname))
        return files

    def match_backgrounds(self, audio_files, bg_files):
        """Match backgrounds to audio files based on mode."""
        if not bg_files:
            return [None] * len(audio_files)

        if self.bg_mode == "Match by Filename":
            matched = []
            for audio in audio_files:
                audio_base = os.path.splitext(os.path.basename(audio))[0].lower()
                found = None
                for bg in bg_files:
                    bg_base = os.path.splitext(os.path.basename(bg))[0].lower()
                    if audio_base == bg_base:
                        found = bg
                        break
                matched.append(found or bg_files[0])
            return matched

        elif self.bg_mode == "Sequential Background":
            return [bg_files[i % len(bg_files)] for i in range(len(audio_files))]

        else:
            return [random.choice(bg_files) for _ in range(len(audio_files))]

    def prepare_jobs(self):
        """Prepare batch rendering jobs."""
        audio_files = self.scan_audio_files()
        bg_files = self.scan_background_files()
        backgrounds = self.match_backgrounds(audio_files, bg_files)

        self._jobs = []
        for i, audio in enumerate(audio_files):
            name = os.path.splitext(os.path.basename(audio))[0]
            output = os.path.join(self.output_folder, f"{safe_filename(name)}.mp4")
            job = {
                "index": i + 1,
                "audio_path": audio,
                "background_path": backgrounds[i],
                "output_path": output,
                "name": name,
                "status": "pending",
                "error": None,
            }
            self._jobs.append(job)

        return self._jobs

    def get_jobs(self):
        return self._jobs

    def save_report(self):
        """Save batch render report."""
        report_path = os.path.join(DIRS["logs"], "batch_report.csv")
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["#", "Name", "Audio", "Background", "Output", "Status", "Error"])
            for job in self._jobs:
                writer.writerow([
                    job["index"], job["name"], job["audio_path"],
                    job["background_path"] or "None", job["output_path"],
                    job["status"], job["error"] or ""
                ])
        logger.info(f"Batch report saved: {report_path}")
        return report_path


class BatchRenderThread(QThread):
    """Background thread for batch rendering."""
    progress = pyqtSignal(int, str)
    job_started = pyqtSignal(int, str)
    job_finished = pyqtSignal(int, str, str)
    job_error = pyqtSignal(int, str, str)
    all_finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, batch_renderer, render_settings):
        super().__init__()
        self.batch = batch_renderer
        self.render_settings = render_settings
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            from app.audio.analyzer import AudioAnalyzer
            from app.lyrics.metadata_lyrics_extractor import MetadataLyricsExtractor
            from app.lyrics.whisper_engine import WhisperEngine, segments_to_lyrics_data
            from app.lyrics.karaoke_engine import KaraokeEngine
            from app.visual.spectrum_renderer import SpectrumRenderer
            from app.render.video_renderer import VideoRenderer

            jobs = self.batch.get_jobs()
            total = len(jobs)

            for i, job in enumerate(jobs):
                if self._cancel:
                    self.progress.emit(0, "Batch cancelled")
                    return

                self.job_started.emit(job["index"], job["name"])
                self.progress.emit(int(i / total * 100), f"Processing {i + 1}/{total}: {job['name']}")

                try:
                    analyzer = AudioAnalyzer(job["audio_path"])
                    if analyzer.load_cache(DIRS["cache"]):
                        self.progress.emit(int(i / total * 100), f"Loaded cached analysis: {job['name']}")
                    else:
                        analyzer.load_audio()
                        analyzer.compute_spectrum()
                        analyzer.detect_beats()
                        analyzer.save_cache(DIRS["cache"])

                    lyrics_data = None
                    if self.batch.use_metadata:
                        extractor = MetadataLyricsExtractor(job["audio_path"])
                        lyrics_data = extractor.extract_metadata()

                    if self.batch.auto_lyrics and (not lyrics_data or not lyrics_data.has_synced):
                        try:
                            engine = WhisperEngine(
                                model_name=self.render_settings.get("whisper_model", "Auto Best Model"),
                                device=self.render_settings.get("device", "auto"),
                                compute_type=self.render_settings.get("compute_type", "auto"),
                            )
                            engine.load_model()
                            result = engine.transcribe(job["audio_path"])
                            lyrics_data = segments_to_lyrics_data(result)
                        except Exception as e:
                            logger.warning(f"Whisper failed for {job['name']}: {e}")

                    karaoke = KaraokeEngine(lyrics_data)
                    karaoke.mode = self.render_settings.get("karaoke_mode", "Karaoke Word Highlight")

                    renderer = VideoRenderer(self.render_settings)
                    renderer.set_audio(job["audio_path"], analyzer, analyzer.duration)
                    renderer.set_background(job["background_path"])
                    renderer.set_output(job["output_path"])

                    spectrum = SpectrumRenderer(
                        self.render_settings.get("width", 1920),
                        self.render_settings.get("height", 1080),
                        self.render_settings.get("spectrum_style", "Bar Spectrum"),
                    )
                    renderer.spectrum_renderer = spectrum
                    renderer.karaoke_engine = karaoke

                    render_thread_inner = _InnerRenderWorker(renderer)
                    render_thread_inner.run()

                    if render_thread_inner.error_msg:
                        raise Exception(render_thread_inner.error_msg)

                    job["status"] = "completed"
                    self.job_finished.emit(job["index"], job["name"], job["output_path"])

                except Exception as e:
                    job["status"] = "failed"
                    job["error"] = str(e)
                    self.job_error.emit(job["index"], job["name"], str(e))
                    logger.error(f"Batch job failed: {job['name']}: {e}")

            report = self.batch.save_report()
            self.progress.emit(100, "Batch render complete!")
            self.all_finished.emit(report)

        except Exception as e:
            logger.error(f"Batch render error: {e}")
            self.error.emit(str(e))


class _InnerRenderWorker:
    """Synchronous inner render worker for batch mode."""
    def __init__(self, renderer):
        self.renderer = renderer
        self.error_msg = None

    def run(self):
        import subprocess
        import numpy as np
        import time

        r = self.renderer
        try:
            bg = r._load_background()
            is_video_bg = isinstance(bg, str) and bg == "video"
            total_frames = int(r.duration * r.fps)

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{r.width}x{r.height}",
                "-pix_fmt", "rgb24", "-r", str(r.fps),
                "-i", "-",
                "-i", r.audio_path,
                "-c:v", "libx264", "-preset", r.ffmpeg_preset,
                "-crf", "18", "-c:a", "aac", "-b:a", "192k",
                "-shortest", "-pix_fmt", "yuv420p",
                r.output_path,
            ]

            process = subprocess.Popen(
                ffmpeg_cmd, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )

            bg_proc = None
            bg_gen = None
            if is_video_bg and r.background_path:
                bg_cmd = [
                    "ffmpeg", "-y", "-stream_loop", "-1",
                    "-i", r.background_path,
                    "-vf", f"scale={r.width}:{r.height}",
                    "-f", "rawvideo", "-pix_fmt", "rgb24",
                    "-r", str(r.fps), "-v", "quiet", "-",
                ]
                bg_proc = subprocess.Popen(bg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                frame_size = r.width * r.height * 3

                def gen():
                    while True:
                        data = bg_proc.stdout.read(frame_size)
                        if len(data) < frame_size:
                            break
                        yield data
                bg_gen = gen()

            for fn in range(total_frames):
                t = fn / r.fps
                if is_video_bg and bg_gen:
                    try:
                        raw = next(bg_gen)
                        bg_frame = Image.frombytes("RGB", (r.width, r.height), raw)
                    except StopIteration:
                        bg_frame = Image.new("RGB", (r.width, r.height), (20, 20, 30))
                else:
                    bg_frame = bg.copy() if isinstance(bg, Image.Image) else Image.new("RGB", (r.width, r.height), (20, 20, 30))

                frame = r.render_frame(bg_frame, t)
                try:
                    process.stdin.write(np.array(frame).tobytes())
                except BrokenPipeError:
                    break

            process.stdin.close()
            process.wait()
            if bg_proc:
                bg_proc.terminate()

            if process.returncode != 0:
                self.error_msg = process.stderr.read().decode()[-300:]

        except Exception as e:
            self.error_msg = str(e)
