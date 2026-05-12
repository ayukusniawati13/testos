"""Font discovery + caching for the PIL text renderer."""

from __future__ import annotations

import logging
import os
import sys
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

logger = logging.getLogger(__name__)


_SEARCH_DIRS: list[Path] = []


def _collect_dirs() -> list[Path]:
    if _SEARCH_DIRS:
        return _SEARCH_DIRS
    candidates: list[Path] = []
    if sys.platform.startswith("win"):
        win_dir = Path(os.environ.get("WINDIR", "C:/Windows"))
        candidates.append(win_dir / "Fonts")
        local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        candidates.append(local / "Microsoft" / "Windows" / "Fonts")
    elif sys.platform == "darwin":
        candidates += [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library" / "Fonts",
        ]
    else:
        candidates += [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
            Path.home() / ".local" / "share" / "fonts",
        ]
    candidates.append(Path(__file__).resolve().parent.parent / "resources" / "fonts")
    _SEARCH_DIRS.extend(p for p in candidates if p.exists())
    return _SEARCH_DIRS


def list_fonts() -> list[tuple[str, str]]:
    """Return list of (family, path) tuples. Family is a friendly name."""
    seen: dict[str, str] = {}
    for d in _collect_dirs():
        try:
            for p in d.rglob("*.ttf"):
                seen.setdefault(_family_name(p), str(p))
            for p in d.rglob("*.otf"):
                seen.setdefault(_family_name(p), str(p))
        except OSError as exc:
            logger.debug("Tidak bisa scan folder font %s: %s", d, exc)
    pairs = sorted(seen.items(), key=lambda x: x[0].lower())
    return pairs


def _family_name(p: Path) -> str:
    try:
        font = ImageFont.truetype(str(p), size=20)
        family = font.getname()[0]
        return family or p.stem
    except Exception:
        return p.stem


@lru_cache(maxsize=64)
def load_font(family: str, size: int) -> ImageFont.FreeTypeFont:
    families = dict(list_fonts())
    path = families.get(family)
    if path and os.path.exists(path):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError as exc:
            logger.debug("Font %s gagal dimuat (%s); fallback", family, exc)
    # Try common fallbacks
    for candidate in (
        "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial.ttf", "Arial Bold.ttf", "arial.ttf",
        "NotoSans-Regular.ttf", "NotoSans-Bold.ttf",
    ):
        for d in _collect_dirs():
            for found in d.rglob(candidate):
                try:
                    return ImageFont.truetype(str(found), size=size)
                except OSError:
                    continue
    return ImageFont.load_default()
