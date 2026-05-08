"""
Karaoke rendering engine - manages lyrics display timing and mode selection.
"""
import logging

logger = logging.getLogger(__name__)


class KaraokeEngine:
    """Core karaoke engine that manages lyrics display and timing."""

    def __init__(self, lyrics_data=None):
        self.lyrics_data = lyrics_data
        self.mode = "Karaoke Word Highlight"
        self.settings = {
            "font_family": "Arial",
            "font_size": 42,
            "normal_color": "#888888",
            "highlight_color": "#ffffff",
            "outline_color": "#000000",
            "outline_thickness": 2,
            "shadow_color": "#000000",
            "shadow_blur": 4,
            "glow_effect": False,
            "glow_intensity": 0.5,
            "opacity": 1.0,
            "letter_spacing": 0,
            "line_spacing": 1.4,
            "transition_speed": 0.3,
            "highlight_anim_speed": 0.2,
            "text_animation": "Fade",
            "lines_visible": 2,
        }
        self.position = {"x": 0.5, "y": 0.75}
        self.sync_offset = 0.0

    def set_lyrics(self, lyrics_data):
        self.lyrics_data = lyrics_data

    def set_mode(self, mode):
        self.mode = mode

    def apply_preset(self, preset_settings):
        if "mode" in preset_settings:
            self.mode = preset_settings["mode"]
        for key, value in preset_settings.items():
            if key != "mode" and key in self.settings:
                self.settings[key] = value

    def get_display_data(self, time_sec):
        """Get karaoke display data for a specific time."""
        if not self.lyrics_data or not self.lyrics_data.lines:
            return None

        adjusted_time = time_sec + self.sync_offset
        current_line = self.lyrics_data.get_line_at_time(adjusted_time)
        if not current_line:
            closest = self._find_closest_line(adjusted_time)
            if closest and abs(closest.start - adjusted_time) < 2.0:
                current_line = closest

        if not current_line:
            return None

        line_idx = self.lyrics_data.lines.index(current_line)
        active_word_idx = self.lyrics_data.get_active_word_index(current_line, adjusted_time)

        word_progress = 0.0
        if active_word_idx >= 0 and current_line.words:
            word = current_line.words[active_word_idx]
            word_progress = self.lyrics_data.get_word_progress(word, adjusted_time)

        line_progress = 0.0
        if current_line.end > current_line.start:
            line_progress = (adjusted_time - current_line.start) / (current_line.end - current_line.start)
            line_progress = max(0.0, min(1.0, line_progress))

        prev_line = self.lyrics_data.lines[line_idx - 1] if line_idx > 0 else None
        next_line = self.lyrics_data.lines[line_idx + 1] if line_idx < len(self.lyrics_data.lines) - 1 else None

        return {
            "mode": self.mode,
            "current_line": current_line,
            "line_index": line_idx,
            "active_word_index": active_word_idx,
            "word_progress": word_progress,
            "line_progress": line_progress,
            "prev_line": prev_line,
            "next_line": next_line,
            "settings": self.settings,
            "position": self.position,
            "time": adjusted_time,
        }

    def _find_closest_line(self, time_sec):
        """Find the closest line to a given time."""
        if not self.lyrics_data or not self.lyrics_data.lines:
            return None
        closest = None
        min_dist = float("inf")
        for line in self.lyrics_data.lines:
            dist = abs(line.start - time_sec)
            if dist < min_dist:
                min_dist = dist
                closest = line
        return closest

    def get_sync_quality(self):
        """Evaluate sync quality of current lyrics."""
        if not self.lyrics_data or not self.lyrics_data.lines:
            return "Failed", "No lyrics data"

        has_word_timing = all(
            len(line.words) > 0 and all(w.start > 0 or w.end > 0 for w in line.words)
            for line in self.lyrics_data.lines if line.text.strip()
        )

        has_line_timing = all(
            line.start > 0 or line.end > 0
            for line in self.lyrics_data.lines if line.text.strip()
        )

        total_lines = len([l for l in self.lyrics_data.lines if l.text.strip()])
        if total_lines == 0:
            return "Failed", "No lyrics lines"

        if has_word_timing and self.lyrics_data.source in ["WhisperX Synced", "Synchronized Metadata"]:
            return "Excellent", f"{total_lines} lines with word-level sync"
        elif has_word_timing:
            return "Good", f"{total_lines} lines with word timestamps"
        elif has_line_timing:
            return "Needs Review", f"{total_lines} lines with line-level timing only"
        else:
            return "Failed", "No timing information"

    def shift_all(self, offset_sec):
        """Shift all lyrics timing."""
        self.sync_offset += offset_sec

    def shift_line(self, line_index, offset_sec):
        """Shift a specific line timing."""
        if self.lyrics_data:
            self.lyrics_data.shift_line(line_index, offset_sec)

    def reset_sync(self):
        """Reset sync offset."""
        self.sync_offset = 0.0

    def export_lrc(self, filepath):
        """Export lyrics as LRC file."""
        if not self.lyrics_data:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            for line in self.lyrics_data.lines:
                t = line.start + self.sync_offset
                minutes = int(t // 60)
                seconds = t % 60
                f.write(f"[{minutes:02d}:{seconds:05.2f}]{line.text}\n")

    def export_srt(self, filepath):
        """Export lyrics as SRT file."""
        if not self.lyrics_data:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            for i, line in enumerate(self.lyrics_data.lines, 1):
                start = line.start + self.sync_offset
                end = line.end + self.sync_offset
                sh, sm, ss = int(start // 3600), int((start % 3600) // 60), start % 60
                eh, em, es = int(end // 3600), int((end % 3600) // 60), end % 60
                f.write(f"{i}\n")
                f.write(f"{sh:02d}:{sm:02d}:{ss:06.3f}".replace(".", ","))
                f.write(f" --> ")
                f.write(f"{eh:02d}:{em:02d}:{es:06.3f}".replace(".", ","))
                f.write(f"\n{line.text}\n\n")
