"""
Extract lyrics from audio file metadata (ID3 tags, USLT, SYLT).
Also handles external .lrc/.srt/.ass files.
"""
import os
import re
import logging

logger = logging.getLogger(__name__)


class LyricsWord:
    """A single word with timing information."""
    def __init__(self, text, start, end):
        self.text = text
        self.start = start
        self.end = end


class LyricsLine:
    """A line of lyrics with timing."""
    def __init__(self, text, start, end, words=None):
        self.text = text
        self.start = start
        self.end = end
        self.words = words or []


class LyricsData:
    """Complete lyrics data with metadata."""
    def __init__(self):
        self.lines = []
        self.source = "Unknown"
        self.language = "auto"
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.cover_data = None
        self.has_synced = False
        self.raw_text = ""

    def get_line_at_time(self, time_sec):
        for line in self.lines:
            if line.start <= time_sec <= line.end:
                return line
        return None

    def get_active_word_index(self, line, time_sec):
        if not line or not line.words:
            return -1
        for i, word in enumerate(line.words):
            if word.start <= time_sec <= word.end:
                return i
        return -1

    def get_word_progress(self, word, time_sec):
        if not word or word.end <= word.start:
            return 0.0
        progress = (time_sec - word.start) / (word.end - word.start)
        return max(0.0, min(1.0, progress))

    def shift_all(self, offset_sec):
        for line in self.lines:
            line.start += offset_sec
            line.end += offset_sec
            for word in line.words:
                word.start += offset_sec
                word.end += offset_sec

    def shift_line(self, line_index, offset_sec):
        if 0 <= line_index < len(self.lines):
            line = self.lines[line_index]
            line.start += offset_sec
            line.end += offset_sec
            for word in line.words:
                word.start += offset_sec
                word.end += offset_sec


class MetadataLyricsExtractor:
    """Extract lyrics and metadata from audio files."""

    def __init__(self, filepath):
        self.filepath = filepath

    def extract_metadata(self):
        """Extract all metadata from the audio file."""
        data = LyricsData()
        ext = os.path.splitext(self.filepath)[1].lower()

        try:
            if ext == ".mp3":
                self._extract_mp3(data)
            elif ext == ".flac":
                self._extract_flac(data)
            elif ext == ".m4a":
                self._extract_m4a(data)
            elif ext == ".wav":
                self._extract_wav(data)
        except Exception as e:
            logger.warning(f"Metadata extraction error: {e}")

        external = self._find_external_lyrics()
        if external:
            ext_data = self._parse_external_lyrics(external)
            if ext_data and not data.has_synced:
                data.lines = ext_data.lines
                data.has_synced = ext_data.has_synced
                data.source = ext_data.source

        return data

    def _extract_mp3(self, data):
        """Extract from MP3 ID3 tags."""
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3
        except ImportError:
            logger.warning("mutagen not installed")
            return

        try:
            audio = MP3(self.filepath)
            tags = audio.tags
            if not tags:
                return

            data.title = str(tags.get("TIT2", ""))
            data.artist = str(tags.get("TPE1", ""))
            data.album = str(tags.get("TALB", ""))
            data.year = str(tags.get("TDRC", ""))
            data.genre = str(tags.get("TCON", ""))

            apic_keys = [k for k in tags.keys() if k.startswith("APIC")]
            if apic_keys:
                data.cover_data = tags[apic_keys[0]].data

            sylt_keys = [k for k in tags.keys() if k.startswith("SYLT")]
            if sylt_keys:
                sylt = tags[sylt_keys[0]]
                self._parse_sylt(sylt, data)
                data.source = "Synchronized Metadata"
                data.has_synced = True
                logger.info("Found SYLT synchronized lyrics")
                return

            uslt_keys = [k for k in tags.keys() if k.startswith("USLT")]
            if uslt_keys:
                uslt = tags[uslt_keys[0]]
                data.raw_text = str(uslt)
                self._parse_plain_lyrics(str(uslt), data)
                data.source = "Metadata Lyrics"
                logger.info("Found USLT lyrics")

        except Exception as e:
            logger.error(f"MP3 metadata error: {e}")

    def _extract_flac(self, data):
        """Extract from FLAC metadata."""
        try:
            from mutagen.flac import FLAC
        except ImportError:
            return

        try:
            audio = FLAC(self.filepath)
            data.title = audio.get("title", [""])[0] if audio.get("title") else ""
            data.artist = audio.get("artist", [""])[0] if audio.get("artist") else ""
            data.album = audio.get("album", [""])[0] if audio.get("album") else ""
            data.year = audio.get("date", [""])[0] if audio.get("date") else ""
            data.genre = audio.get("genre", [""])[0] if audio.get("genre") else ""

            if audio.pictures:
                data.cover_data = audio.pictures[0].data

            lyrics_text = audio.get("lyrics", [""])[0] if audio.get("lyrics") else ""
            if lyrics_text:
                data.raw_text = lyrics_text
                self._parse_plain_lyrics(lyrics_text, data)
                data.source = "Metadata Lyrics"
        except Exception as e:
            logger.error(f"FLAC metadata error: {e}")

    def _extract_m4a(self, data):
        """Extract from M4A/AAC metadata."""
        try:
            from mutagen.mp4 import MP4
        except ImportError:
            return

        try:
            audio = MP4(self.filepath)
            tags = audio.tags or {}
            data.title = tags.get("\xa9nam", [""])[0] if tags.get("\xa9nam") else ""
            data.artist = tags.get("\xa9ART", [""])[0] if tags.get("\xa9ART") else ""
            data.album = tags.get("\xa9alb", [""])[0] if tags.get("\xa9alb") else ""
            data.year = tags.get("\xa9day", [""])[0] if tags.get("\xa9day") else ""
            data.genre = tags.get("\xa9gen", [""])[0] if tags.get("\xa9gen") else ""

            if "covr" in tags:
                data.cover_data = bytes(tags["covr"][0])

            lyrics = tags.get("\xa9lyr", [""])[0] if tags.get("\xa9lyr") else ""
            if lyrics:
                data.raw_text = lyrics
                self._parse_plain_lyrics(lyrics, data)
                data.source = "Metadata Lyrics"
        except Exception as e:
            logger.error(f"M4A metadata error: {e}")

    def _extract_wav(self, data):
        """Extract from WAV metadata (minimal)."""
        try:
            from mutagen.wave import WAVE
            audio = WAVE(self.filepath)
            if audio.tags:
                data.title = str(audio.tags.get("TIT2", ""))
                data.artist = str(audio.tags.get("TPE1", ""))
        except Exception:
            pass

    def _parse_sylt(self, sylt, data):
        """Parse SYLT synchronized lyrics."""
        try:
            lines = []
            current_line_words = []
            current_line_text = ""
            line_start = 0

            for text, timestamp_ms in sylt.text:
                timestamp = timestamp_ms / 1000.0
                text = text.strip()
                if not text:
                    continue

                if text == "\n" or text == "\r\n":
                    if current_line_words:
                        line = LyricsLine(
                            current_line_text.strip(),
                            line_start,
                            timestamp,
                            current_line_words
                        )
                        lines.append(line)
                        current_line_words = []
                        current_line_text = ""
                    line_start = timestamp
                else:
                    word = LyricsWord(text, timestamp, timestamp + 0.5)
                    current_line_words.append(word)
                    current_line_text += text + " "
                    if not current_line_words[:-1]:
                        line_start = timestamp

            if current_line_words:
                line = LyricsLine(
                    current_line_text.strip(),
                    line_start,
                    current_line_words[-1].end,
                    current_line_words
                )
                lines.append(line)

            for i in range(len(lines) - 1):
                lines[i].end = lines[i + 1].start
                if lines[i].words:
                    lines[i].words[-1].end = lines[i + 1].start

            data.lines = lines
        except Exception as e:
            logger.error(f"SYLT parse error: {e}")

    def _parse_plain_lyrics(self, text, data):
        """Parse plain text lyrics (no timing)."""
        lines_text = text.strip().split("\n")
        lines = []
        for lt in lines_text:
            lt = lt.strip()
            if lt:
                line = LyricsLine(lt, 0, 0)
                lines.append(line)
        data.lines = lines

    def _find_external_lyrics(self):
        """Find external .lrc/.srt/.ass file matching the audio."""
        base = os.path.splitext(self.filepath)[0]
        for ext in [".lrc", ".srt", ".ass"]:
            path = base + ext
            if os.path.exists(path):
                return path
        return None

    def _parse_external_lyrics(self, filepath):
        """Parse external lyrics file."""
        ext = os.path.splitext(filepath)[1].lower()
        data = LyricsData()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            try:
                with open(filepath, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception:
                return None

        if ext == ".lrc":
            self._parse_lrc(content, data)
            data.source = "External Lyrics File"
        elif ext == ".srt":
            self._parse_srt(content, data)
            data.source = "External Lyrics File"
        elif ext == ".ass":
            self._parse_ass(content, data)
            data.source = "External Lyrics File"

        return data

    def _parse_lrc(self, content, data):
        """Parse LRC format."""
        pattern = re.compile(r"\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)")
        lines = []

        for line_text in content.split("\n"):
            match = pattern.match(line_text.strip())
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                ms_str = match.group(3)
                if len(ms_str) == 2:
                    ms_str += "0"
                ms = int(ms_str)
                timestamp = minutes * 60 + seconds + ms / 1000.0
                text = match.group(4).strip()
                if text:
                    line = LyricsLine(text, timestamp, timestamp)
                    words = []
                    for w in text.split():
                        words.append(LyricsWord(w, timestamp, timestamp))
                    line.words = words
                    lines.append(line)

        for i in range(len(lines) - 1):
            lines[i].end = lines[i + 1].start
            if lines[i].words:
                word_duration = (lines[i].end - lines[i].start) / len(lines[i].words)
                for j, word in enumerate(lines[i].words):
                    word.start = lines[i].start + j * word_duration
                    word.end = word.start + word_duration

        if lines:
            lines[-1].end = lines[-1].start + 5.0
            if lines[-1].words:
                wd = 5.0 / len(lines[-1].words)
                for j, word in enumerate(lines[-1].words):
                    word.start = lines[-1].start + j * wd
                    word.end = word.start + wd

        data.lines = lines
        data.has_synced = bool(lines)

    def _parse_srt(self, content, data):
        """Parse SRT subtitle format."""
        blocks = re.split(r"\n\s*\n", content.strip())
        lines = []

        for block in blocks:
            block_lines = block.strip().split("\n")
            if len(block_lines) >= 3:
                timing_match = re.match(
                    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
                    block_lines[1]
                )
                if timing_match:
                    g = timing_match.groups()
                    start = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
                    end = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
                    text = " ".join(block_lines[2:]).strip()
                    text = re.sub(r"<[^>]+>", "", text)

                    line = LyricsLine(text, start, end)
                    words = text.split()
                    if words:
                        wd = (end - start) / len(words)
                        line.words = [
                            LyricsWord(w, start + i * wd, start + (i + 1) * wd)
                            for i, w in enumerate(words)
                        ]
                    lines.append(line)

        data.lines = lines
        data.has_synced = bool(lines)

    def _parse_ass(self, content, data):
        """Parse ASS/SSA subtitle format."""
        lines = []
        for raw_line in content.split("\n"):
            raw_line = raw_line.strip()
            if raw_line.startswith("Dialogue:"):
                parts = raw_line.split(",", 9)
                if len(parts) >= 10:
                    start = self._parse_ass_time(parts[1].strip())
                    end = self._parse_ass_time(parts[2].strip())
                    text = parts[9].strip()
                    text = re.sub(r"\{[^}]*\}", "", text)
                    text = text.replace("\\N", " ").replace("\\n", " ")

                    if text:
                        line = LyricsLine(text, start, end)
                        words = text.split()
                        if words:
                            wd = (end - start) / len(words)
                            line.words = [
                                LyricsWord(w, start + i * wd, start + (i + 1) * wd)
                                for i, w in enumerate(words)
                            ]
                        lines.append(line)

        data.lines = lines
        data.has_synced = bool(lines)

    def _parse_ass_time(self, time_str):
        """Parse ASS time format H:MM:SS.CC."""
        try:
            parts = time_str.split(":")
            h = int(parts[0])
            m = int(parts[1])
            s_parts = parts[2].split(".")
            s = int(s_parts[0])
            cs = int(s_parts[1]) if len(s_parts) > 1 else 0
            return h * 3600 + m * 60 + s + cs / 100.0
        except Exception:
            return 0.0
