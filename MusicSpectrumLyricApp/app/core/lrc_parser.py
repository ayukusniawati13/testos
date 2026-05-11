"""LRC file parser with millisecond-precision timestamp support."""

import re
from dataclasses import dataclass


@dataclass
class LyricLine:
    time: float
    text: str


class LRCParser:
    TIMESTAMP_RE = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.+)")

    @staticmethod
    def parse(filepath: str) -> list[LyricLine]:
        lines: list[LyricLine] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                m = LRCParser.TIMESTAMP_RE.match(raw)
                if m:
                    minutes = int(m.group(1))
                    seconds = int(m.group(2))
                    frac = m.group(3)
                    if len(frac) == 2:
                        ms = int(frac) * 10
                    else:
                        ms = int(frac)
                    time_sec = minutes * 60 + seconds + ms / 1000.0
                    text = m.group(4).strip()
                    if text:
                        lines.append(LyricLine(time=time_sec, text=text))
        lines.sort(key=lambda l: l.time)
        return lines

    @staticmethod
    def parse_text(content: str) -> list[LyricLine]:
        lines: list[LyricLine] = []
        for raw in content.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            m = LRCParser.TIMESTAMP_RE.match(raw)
            if m:
                minutes = int(m.group(1))
                seconds = int(m.group(2))
                frac = m.group(3)
                if len(frac) == 2:
                    ms = int(frac) * 10
                else:
                    ms = int(frac)
                time_sec = minutes * 60 + seconds + ms / 1000.0
                text = m.group(4).strip()
                if text:
                    lines.append(LyricLine(time=time_sec, text=text))
        lines.sort(key=lambda l: l.time)
        return lines
