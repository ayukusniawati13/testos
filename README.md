# Spectrum Lyric Video Maker

A professional Python desktop application for generating music videos that
combine **dynamic, modern audio spectrum visualizations** with **automatically
synchronized lyrics**. Designed as a solid foundation that you can run today
and extend tomorrow.

> Aplikasi ini dibuat sebagai pondasi profesional, **bukan prototype sederhana**.
> Setiap fitur diorganisir dalam modul terpisah agar mudah dikembangkan.

---

## Features

### Audio input
- Supported formats: `mp3`, `wav`, `flac`, `m4a`, `ogg`, `aac`.
- Drag-and-drop loading.
- Reads duration, sample rate, channels, and embedded metadata.

### Auto lyrics
- Speech-to-text via `faster-whisper`, with word-level timestamps.
- Optional `stable-ts` integration for tighter forced-alignment.
- Manual import/export of `.txt`, `.srt`, `.lrc`.
- Editable transcript before render.
- Display modes: per-line, karaoke word-by-word, highlight current word, fade in/out.

### Audio spectrum
- Six built-in visualizers — **bar**, **circular**, **wave**, **radial**,
  **particle**, and **glow**.
- Reactivity to overall energy, bass, mid, and treble bands plus beat detection.
- Smoothing for fluid motion.
- Color modes: gradient, neon, rainbow, custom, auto-from-background.
- Effects: glow, blur, shadow, pulse-on-beat, particles, reflection.
- Free positioning: X, Y, scale, rotation, opacity, anchor.

### Background
- Image, video, folder of backgrounds, solid color, gradient.
- Output sizes: 1920x1080, 1080x1920, 1080x1080, custom.
- Fit modes: cover, contain, stretch, blur-fill.

### Optional logo
- PNG / JPG with corner presets or custom X/Y, size, opacity, margin, fade.

### Optional animation overlay
- `mp4`, `mov`, `webm`, `gif` overlays placed at start, middle, end, or
  custom timestamp, with duration / position / opacity / blend controls.

### Batch processing
- Pick a music folder + background folder.
- Match strategies: random, same-name, by orientation/size, single-for-all.
- Queue with `waiting / processing / done / failed` state.
- Pause / cancel without losing progress.
- Auto-saves each video to the configured output folder.

### Render engine
- FFmpeg-based pipeline (H.264 by default, H.265 optional).
- Configurable resolution, fps (24/30/60), bitrate, CRF, preset, audio bitrate.
- Per-render percentage progress.
- Runs on a worker thread so the GUI stays responsive.

### FFmpeg checker
- Detects FFmpeg on startup (status: *installed* / *not found*).
- "Install FFmpeg Online" downloads a static build for the current OS,
  extracts it locally, and adds it to the app's path.
- Falls back to manual instructions if the auto-install fails.

### Logging
- Rich panel inside the app + persistent log file at `logs/app.log`.
- Captures: file processed, errors, render progress, FFmpeg status,
  transcription status, batch results.

### UI / UX
- Dark modern theme (Qt stylesheet) -- sidebar, main workspace, preview,
  settings, render queue, log panel.
- Modes: **Single Project**, **Batch Mode**, **Presets**, **Settings**, **Logs**.
- Save/load spectrum + lyric presets.

---

## Project layout

```
spectrum_lyric_video_maker/
├── app/
│   ├── main.py                 # QApplication bootstrap
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── widgets/            # sidebar, panels, preview, log...
│   │   ├── dialogs/            # ffmpeg, presets, settings dialogs
│   │   └── themes/             # dark_modern.qss
│   ├── core/
│   │   ├── audio_analyzer.py   # librosa-based spectrum + beat analysis
│   │   ├── spectrum_engine.py  # bar / circular / wave / radial / particle / glow
│   │   ├── lyric_engine.py     # Whisper, SRT/LRC IO, alignment helpers
│   │   ├── render_engine.py    # FFmpeg pipeline + worker thread
│   │   ├── batch_processor.py  # queue, pause/cancel, matching strategies
│   │   ├── ffmpeg_manager.py   # detect + auto-install
│   │   └── project_manager.py  # presets / project files
│   ├── utils/
│   │   ├── logger.py
│   │   ├── file_utils.py
│   │   ├── config.py
│   │   └── validators.py
│   └── assets/
│       ├── icons/
│       ├── themes/
│       └── presets/
├── output/                     # rendered videos go here
├── logs/                       # app.log lives here
├── temp/                       # frame caches, transient files
├── presets/                    # user-saved presets
├── installer/                  # installer scripts / metadata
├── requirements.txt
├── README.md
├── build.py                    # PyInstaller build helper
└── run.py                      # entry point: `python run.py`
```

---

## Quick start

### 1. Install Python dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> `faster-whisper` will pull `ctranslate2`. The first transcription downloads
> a Whisper model (default: `base`) into `~/.cache`.

### 2. Make sure FFmpeg is reachable

The application checks for FFmpeg on startup. If it isn't found, click
**Install FFmpeg Online** in the FFmpeg dialog -- the app downloads a static
build for your OS into `app/assets/ffmpeg/` and uses it from there.

You can also rely on a system-wide install (`apt`, `brew`, `choco`, ...).

### 3. Run

```bash
python run.py
```

### 4. Build a desktop executable (optional)

```bash
python build.py            # one-folder bundle
python build.py --onefile  # single executable file
```

---

## Development notes

- All long-running work (transcription, FFmpeg, batch processing) runs on
  worker threads via Qt's `QThread` so the GUI never freezes.
- Heavy dependencies (`librosa`, `faster_whisper`, `cv2`) are imported lazily
  the first time they're actually needed, so the app launches quickly.
- Configuration lives in `~/.spectrum_lyric_video_maker/config.json`.
- Logs are written to `logs/app.log` (rotating) and mirrored to the in-app log
  panel.
- The code is fully type-hinted and organized in small modules. Read
  `app/core/*.py` to see how each concern is isolated.

---

## License

MIT.
