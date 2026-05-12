"""Batch mode helpers: match audio files to background files."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

from ..utils.paths import list_audio_files, list_visual_files, safe_stem

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    audio_path: str
    background_files: list[str]


def build_batch(
    music_folder: str,
    background_folder: str,
    match_mode: str,
    multi_background: bool = False,
) -> list[BatchJob]:
    audios = list_audio_files(music_folder)
    backgrounds = list_visual_files(background_folder)
    if not audios:
        return []
    if not backgrounds:
        return [BatchJob(audio_path=a, background_files=[]) for a in audios]

    jobs: list[BatchJob] = []
    if match_mode == "name":
        for audio in audios:
            stem = safe_stem(audio).lower()
            matches = [b for b in backgrounds if safe_stem(b).lower().startswith(stem) or stem.startswith(safe_stem(b).lower())]
            files = matches if matches else [backgrounds[len(jobs) % len(backgrounds)]]
            if not multi_background:
                files = files[:1]
            jobs.append(BatchJob(audio_path=audio, background_files=files))
    elif match_mode == "random":
        for audio in audios:
            n = random.randint(1, 3) if multi_background else 1
            files = random.sample(backgrounds, min(n, len(backgrounds)))
            jobs.append(BatchJob(audio_path=audio, background_files=files))
    else:  # order
        for i, audio in enumerate(audios):
            if multi_background:
                files = [backgrounds[(i + k) % len(backgrounds)] for k in range(min(3, len(backgrounds)))]
            else:
                files = [backgrounds[i % len(backgrounds)]]
            jobs.append(BatchJob(audio_path=audio, background_files=files))
    return jobs
