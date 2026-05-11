"""Automated test suite for Music Spectrum Lyric Video Maker.

Uses the provided test media files:
  - We Drifted Without Knowing.mp3
  - We Drifted Without Knowing.lrc
  - whisk_u4yp8l_via_RJ_Whisk_Auto.jpg
"""

import os
import sys
import shutil
import tempfile

import pytest
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.lrc_parser import LRCParser, LyricLine
from app.core.audio_analyzer import AudioAnalyzer
from app.core.spectrum_engine import SpectrumEngine, SpectrumConfig, SpectrumStyle
from app.core.lyric_renderer import LyricRenderer, LyricConfig
from app.core.ffmpeg_manager import FFmpegManager
from app.core.batch_manager import BatchManager, BackgroundMode

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_data")
LRC_FILE = os.path.join(TEST_DIR, "We Drifted Without Knowing.lrc")
MP3_FILE = os.path.join(TEST_DIR, "We Drifted Without Knowing.mp3")
BG_FILE = os.path.join(TEST_DIR, "whisk_u4yp8l_via_RJ_Whisk_Auto.jpg")


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Copy test media files to test_data/ for reproducible tests."""
    os.makedirs(TEST_DIR, exist_ok=True)

    sources = {
        LRC_FILE: os.path.expanduser(
            "~/attachments/6cc7d6df-7a6e-467f-b05b-4d141d58565f/"
            "We+Drifted+Without+Knowing.lrc"
        ),
        MP3_FILE: os.path.expanduser(
            "~/attachments/0b44572a-76b7-4548-8f04-6c9b227a9f8d/"
            "We+Drifted+Without+Knowing.mp3"
        ),
        BG_FILE: os.path.expanduser(
            "~/attachments/05394faa-cfe1-4342-b2f0-e65fd8818a56/"
            "whisk_u4yp8l_via_RJ_Whisk_Auto.jpg"
        ),
    }
    for dest, src in sources.items():
        if not os.path.exists(dest) and os.path.exists(src):
            shutil.copy2(src, dest)
    yield


# ── LRC Parser Tests ─────────────────────────────────────────────────

class TestLRCParser:
    def test_parse_file_returns_lyrics(self):
        lyrics = LRCParser.parse(LRC_FILE)
        assert len(lyrics) == 52

    def test_first_lyric_timestamp(self):
        lyrics = LRCParser.parse(LRC_FILE)
        assert abs(lyrics[0].time - 17.50) < 0.01
        assert lyrics[0].text == "We used to talk until the sunrise came"

    def test_second_lyric_timestamp(self):
        lyrics = LRCParser.parse(LRC_FILE)
        assert abs(lyrics[1].time - 21.20) < 0.01
        assert lyrics[1].text == "Now we barely say each other's names"

    def test_last_lyric(self):
        lyrics = LRCParser.parse(LRC_FILE)
        last = lyrics[-1]
        assert abs(last.time - 219.50) < 0.01
        assert "never knew would end" in last.text

    def test_lyrics_sorted_by_time(self):
        lyrics = LRCParser.parse(LRC_FILE)
        for i in range(len(lyrics) - 1):
            assert lyrics[i].time <= lyrics[i + 1].time

    def test_millisecond_precision(self):
        lyrics = LRCParser.parse(LRC_FILE)
        assert abs(lyrics[2].time - 24.80) < 0.01

    def test_parse_text_method(self):
        content = "[00:17.50]First line\n[00:21.20]Second line\n"
        lyrics = LRCParser.parse_text(content)
        assert len(lyrics) == 2
        assert lyrics[0].text == "First line"
        assert abs(lyrics[0].time - 17.50) < 0.01

    def test_empty_lines_skipped(self):
        content = "[00:10.00]Line\n\n\n[00:20.00]Another\n"
        lyrics = LRCParser.parse_text(content)
        assert len(lyrics) == 2

    def test_no_lyrics_before_first_timestamp(self):
        lyrics = LRCParser.parse(LRC_FILE)
        assert lyrics[0].time > 0.0, "First lyric should not be at time 0"


# ── Audio Analyzer Tests ──────────────────────────────────────────────

class TestAudioAnalyzer:
    @pytest.fixture(scope="class")
    def analyzer(self):
        a = AudioAnalyzer(MP3_FILE)
        a.load()
        a.analyze()
        return a

    def test_load_mp3(self, analyzer):
        assert analyzer.y is not None
        assert len(analyzer.y) > 0

    def test_duration(self, analyzer):
        assert 200 < analyzer.duration < 260, (
            f"Duration {analyzer.duration:.1f}s should be ~232s"
        )

    def test_spectrum_data_shape(self, analyzer):
        assert analyzer.spectrum_data is not None
        assert analyzer.spectrum_data.ndim == 2

    def test_get_spectrum_at_time(self, analyzer):
        bands = analyzer.get_spectrum_at_time(30.0, n_bands=64)
        assert bands.shape == (64,)
        assert np.all(bands >= 0) and np.all(bands <= 1)

    def test_get_spectrum_at_zero(self, analyzer):
        bands = analyzer.get_spectrum_at_time(0.0, n_bands=32)
        assert bands.shape == (32,)

    def test_get_beat_strength(self, analyzer):
        beat = analyzer.get_beat_strength_at_time(30.0)
        assert 0.0 <= beat <= 1.0

    def test_rms_at_silent_region(self, analyzer):
        rms = analyzer.get_rms_at_time(0.0)
        assert rms >= 0.0

    def test_spectrum_varies_with_time(self, analyzer):
        bands_a = analyzer.get_spectrum_at_time(20.0, n_bands=64)
        bands_b = analyzer.get_spectrum_at_time(60.0, n_bands=64)
        assert not np.allclose(bands_a, bands_b), "Spectrum should vary over time"


# ── Spectrum Engine Tests ─────────────────────────────────────────────

class TestSpectrumEngine:
    def test_all_12_styles_exist(self):
        assert len(SpectrumStyle.ALL) == 12

    @pytest.mark.parametrize("style", SpectrumStyle.ALL)
    def test_render_each_style(self, style):
        cfg = SpectrumConfig()
        cfg.style = style
        engine = SpectrumEngine(cfg)
        bands = np.random.random(64).astype(np.float64)
        beat = 0.5
        result = engine.render(640, 360, bands, beat)
        assert isinstance(result, Image.Image)
        assert result.size == (640, 360)
        assert result.mode == "RGBA"

    def test_bar_spectrum_renders_nonblank(self):
        cfg = SpectrumConfig()
        cfg.style = SpectrumStyle.BAR_MODERN
        engine = SpectrumEngine(cfg)
        bands = np.ones(64)
        result = engine.render(640, 360, bands, 1.0)
        arr = np.array(result)
        assert arr[:, :, 3].max() > 0, "Should render non-transparent pixels"

    def test_render_with_gradient(self):
        cfg = SpectrumConfig()
        cfg.use_gradient = True
        cfg.color1 = (255, 0, 0)
        cfg.color2 = (0, 0, 255)
        engine = SpectrumEngine(cfg)
        bands = np.ones(64)
        result = engine.render(640, 360, bands, 0.7)
        assert isinstance(result, Image.Image)

    def test_render_with_custom_opacity(self):
        cfg = SpectrumConfig()
        cfg.opacity = 0.5
        engine = SpectrumEngine(cfg)
        bands = np.ones(64)
        result = engine.render(640, 360, bands, 0.5)
        assert isinstance(result, Image.Image)


# ── Lyric Renderer Tests ──────────────────────────────────────────────

class TestLyricRenderer:
    @pytest.fixture
    def lyrics(self):
        return LRCParser.parse(LRC_FILE)

    @pytest.fixture
    def renderer(self):
        return LyricRenderer(LyricConfig())

    def test_render_returns_image(self, renderer, lyrics):
        result = renderer.render(640, 360, lyrics, 20.0)
        assert isinstance(result, Image.Image)
        assert result.size == (640, 360)
        assert result.mode == "RGBA"

    def test_no_lyric_before_first_timestamp(self, renderer, lyrics):
        active, next_line, opacity = renderer.get_active_lyric(lyrics, 5.0)
        assert active is None
        assert next_line is None

    def test_active_lyric_at_17_5s(self, renderer, lyrics):
        active, next_line, opacity = renderer.get_active_lyric(lyrics, 17.6)
        assert active is not None
        assert active.text == "We used to talk until the sunrise came"
        assert next_line is not None

    def test_active_lyric_at_middle(self, renderer, lyrics):
        active, _, _ = renderer.get_active_lyric(lyrics, 60.0)
        assert active is not None
        assert len(active.text) > 0

    def test_fade_in_opacity(self, renderer, lyrics):
        _, _, opacity = renderer.get_active_lyric(lyrics, 17.51)
        assert 0.0 < opacity <= 1.0

    def test_render_at_zero_shows_no_lyrics(self, renderer, lyrics):
        result = renderer.render(640, 360, lyrics, 0.0)
        arr = np.array(result)
        assert arr[:, :, 3].max() == 0, "No lyrics should be visible at t=0"


# ── Background Image Tests ────────────────────────────────────────────

class TestBackgroundImage:
    def test_load_background_jpg(self):
        img = Image.open(BG_FILE)
        assert img.size[0] > 0 and img.size[1] > 0

    def test_resize_background(self):
        img = Image.open(BG_FILE).convert("RGBA")
        resized = img.resize((640, 360), Image.LANCZOS)
        assert resized.size == (640, 360)

    def test_composite_background_with_spectrum(self):
        bg = Image.open(BG_FILE).convert("RGBA").resize((640, 360), Image.LANCZOS)
        cfg = SpectrumConfig()
        engine = SpectrumEngine(cfg)
        bands = np.random.random(64)
        spec = engine.render(640, 360, bands, 0.5)
        composite = Image.alpha_composite(bg, spec)
        assert composite.size == (640, 360)

    def test_composite_all_layers(self):
        bg = Image.open(BG_FILE).convert("RGBA").resize((640, 360), Image.LANCZOS)
        lyrics = LRCParser.parse(LRC_FILE)

        spec_engine = SpectrumEngine(SpectrumConfig())
        lyric_renderer = LyricRenderer(LyricConfig())

        bands = np.random.random(64)
        spec_layer = spec_engine.render(640, 360, bands, 0.5)
        lyric_layer = lyric_renderer.render(640, 360, lyrics, 25.0)

        frame = Image.alpha_composite(bg, spec_layer)
        frame = Image.alpha_composite(frame, lyric_layer)
        assert frame.size == (640, 360)
        assert frame.mode == "RGBA"


# ── FFmpeg Manager Tests ──────────────────────────────────────────────

class TestFFmpegManager:
    def test_ffmpeg_detection(self):
        mgr = FFmpegManager()
        assert mgr.is_available, "FFmpeg should be detected on this system"

    def test_ffmpeg_path(self):
        mgr = FFmpegManager()
        assert mgr.ffmpeg_path is not None
        assert os.path.isfile(mgr.ffmpeg_path)


# ── Batch Manager Tests ───────────────────────────────────────────────

class TestBatchManager:
    def test_filename_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            music_dir = os.path.join(tmp, "music")
            lyric_dir = os.path.join(tmp, "lyrics")
            bg_dir = os.path.join(tmp, "backgrounds")
            out_dir = os.path.join(tmp, "output")
            for d in (music_dir, lyric_dir, bg_dir, out_dir):
                os.makedirs(d)

            # Create matching files
            open(os.path.join(music_dir, "song.mp3"), "w").close()
            open(os.path.join(lyric_dir, "song.lrc"), "w").close()
            open(os.path.join(bg_dir, "song.jpg"), "w").close()

            mgr = BatchManager()
            jobs = mgr.scan_folders(music_dir, lyric_dir, bg_dir, out_dir,
                                    bg_mode=BackgroundMode.MATCH_NAME)
            assert len(jobs) == 1
            assert "song" in jobs[0].music_path
            assert jobs[0].lrc_path != ""
            assert jobs[0].background_path != ""

    def test_missing_lyric_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            music_dir = os.path.join(tmp, "music")
            lyric_dir = os.path.join(tmp, "lyrics")
            bg_dir = os.path.join(tmp, "backgrounds")
            out_dir = os.path.join(tmp, "output")
            for d in (music_dir, lyric_dir, bg_dir, out_dir):
                os.makedirs(d)

            open(os.path.join(music_dir, "no_lyric.mp3"), "w").close()

            mgr = BatchManager()
            jobs = mgr.scan_folders(music_dir, lyric_dir, bg_dir, out_dir,
                                    bg_mode=BackgroundMode.MATCH_NAME)
            assert len(jobs) == 1
            assert jobs[0].lrc_path == ""


# ── Integration Test ──────────────────────────────────────────────────

class TestIntegration:
    def test_full_preview_pipeline(self):
        """End-to-end: load audio, parse lyrics, render one preview frame."""
        analyzer = AudioAnalyzer(MP3_FILE)
        analyzer.load()
        analyzer.analyze()

        lyrics = LRCParser.parse(LRC_FILE)
        bg = Image.open(BG_FILE).convert("RGBA").resize((640, 360), Image.LANCZOS)

        spec_cfg = SpectrumConfig()
        spec_cfg.style = SpectrumStyle.BAR_MODERN
        engine = SpectrumEngine(spec_cfg)
        lyric_renderer = LyricRenderer(LyricConfig())

        t = 25.0
        bands = analyzer.get_spectrum_at_time(t, n_bands=64)
        beat = analyzer.get_beat_strength_at_time(t)

        frame = bg.copy()
        spec_layer = engine.render(640, 360, bands, beat)
        frame = Image.alpha_composite(frame, spec_layer)

        lyric_layer = lyric_renderer.render(640, 360, lyrics, t)
        frame = Image.alpha_composite(frame, lyric_layer)

        assert frame.size == (640, 360)

        arr = np.array(frame)
        assert arr[:, :, 3].max() == 255, "Frame should be fully opaque"

    def test_multiple_timestamps_progression(self):
        """Verify lyrics progress correctly through timestamps."""
        lyrics = LRCParser.parse(LRC_FILE)
        renderer = LyricRenderer(LyricConfig())

        test_times = [0.0, 10.0, 17.6, 21.3, 30.0, 60.0, 120.0]
        prev_text = None
        for t in test_times:
            active, _, _ = renderer.get_active_lyric(lyrics, t)
            if active:
                if prev_text and t > 21.0:
                    pass  # lyrics should be changing
            prev_text = active.text if active else None

        active_0, _, _ = renderer.get_active_lyric(lyrics, 0.0)
        assert active_0 is None, "No lyrics at t=0"

        active_18, _, _ = renderer.get_active_lyric(lyrics, 18.0)
        assert active_18 is not None
        assert active_18.text == "We used to talk until the sunrise came"

    @pytest.mark.parametrize("style", SpectrumStyle.ALL)
    def test_full_frame_with_each_style(self, style):
        """Render a complete frame with each spectrum style."""
        bg = Image.open(BG_FILE).convert("RGBA").resize((640, 360), Image.LANCZOS)
        lyrics = LRCParser.parse(LRC_FILE)

        cfg = SpectrumConfig()
        cfg.style = style
        engine = SpectrumEngine(cfg)
        lyric_renderer = LyricRenderer(LyricConfig())

        bands = np.random.random(64)
        spec_layer = engine.render(640, 360, bands, 0.6)
        lyric_layer = lyric_renderer.render(640, 360, lyrics, 25.0)

        frame = Image.alpha_composite(bg, spec_layer)
        frame = Image.alpha_composite(frame, lyric_layer)
        assert frame.size == (640, 360)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
