"""
Render queue manager for sequential rendering of multiple projects.
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from collections import deque

logger = logging.getLogger(__name__)


class RenderJob:
    """A single render job in the queue."""
    def __init__(self, name, renderer, priority=0):
        self.name = name
        self.renderer = renderer
        self.priority = priority
        self.status = "queued"
        self.progress = 0
        self.error = None
        self.output_path = None


class RenderQueue(QObject):
    """Manage a queue of render jobs."""
    job_started = pyqtSignal(str)
    job_progress = pyqtSignal(str, int, str)
    job_finished = pyqtSignal(str, str)
    job_error = pyqtSignal(str, str)
    queue_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._queue = deque()
        self._current_thread = None
        self._is_running = False

    def add_job(self, job):
        self._queue.append(job)
        logger.info(f"Job added to queue: {job.name}")

    def remove_job(self, name):
        self._queue = deque(j for j in self._queue if j.name != name)

    def clear(self):
        self._queue.clear()

    def get_jobs(self):
        return list(self._queue)

    def start(self):
        if self._is_running:
            return
        self._is_running = True
        self._process_next()

    def stop(self):
        self._is_running = False
        if self._current_thread:
            self._current_thread.cancel()

    def _process_next(self):
        if not self._is_running or not self._queue:
            self._is_running = False
            self.queue_finished.emit()
            return

        job = self._queue.popleft()
        job.status = "rendering"
        self.job_started.emit(job.name)

        from app.render.video_renderer import RenderThread
        self._current_thread = RenderThread(job.renderer)
        self._current_thread.progress.connect(
            lambda p, m: self._on_progress(job, p, m)
        )
        self._current_thread.finished.connect(
            lambda path: self._on_finished(job, path)
        )
        self._current_thread.error.connect(
            lambda e: self._on_error(job, e)
        )
        self._current_thread.start()

    def _on_progress(self, job, pct, msg):
        job.progress = pct
        self.job_progress.emit(job.name, pct, msg)

    def _on_finished(self, job, path):
        job.status = "completed"
        job.output_path = path
        self.job_finished.emit(job.name, path)
        self._process_next()

    def _on_error(self, job, error):
        job.status = "failed"
        job.error = error
        self.job_error.emit(job.name, error)
        self._process_next()
