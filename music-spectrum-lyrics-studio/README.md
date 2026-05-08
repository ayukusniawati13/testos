# Music Spectrum Lyrics Studio

Professional music video creator with audio spectrum visualization, karaoke-style synchronized lyrics, logo branding, CTA animations, batch rendering, and low-spec mode support.

## Quick Start

### Windows
```
1. Extract ZIP
2. Run setup.bat
3. Run run.bat
```

### Linux / macOS
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Installation

### Requirements
- Python 3.9+
- FFmpeg (for video rendering)

### Install FFmpeg

**Windows (winget):**
```
winget install --id Gyan.FFmpeg
```

**Windows (manual):**
1. Download from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your PATH

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Install AI Lyrics (Optional)

For AI-powered lyrics generation, install one of the following:

**Faster-Whisper (Recommended - faster, less memory):**
```bash
pip install faster-whisper
```

**OpenAI Whisper:**
```bash
pip install openai-whisper
```

**WhisperX (Best accuracy):**
```bash
pip install whisperx
```

## How to Render a Video

1. **Select Music** - Click "Select Music File" in the Music tab. Supports MP3, WAV, M4A, FLAC.
2. **Select Background** - Choose an image (JPG, PNG, WEBP) or video (MP4, MOV, WEBM, AVI) in the Background tab.
3. **Configure Spectrum** - Choose spectrum style and preset in the Spectrum tab.
4. **Generate Lyrics** - Click "Generate Lyrics (AI)" in the Lyrics tab, or import .lrc/.srt/.ass files.
5. **Set Karaoke Style** - Choose karaoke mode and preset in the Karaoke tab.
6. **Set Resolution** - Configure resolution, aspect ratio, and quality in the Render tab.
7. **Render** - Click "Start Render" in the Render tab.

## Lyrics Synchronization

### Automatic (AI)
1. Go to **Lyrics** tab
2. Select AI model (Auto Best, Whisper Large-v3, Faster-Whisper, etc.)
3. Click **Generate Lyrics (AI)**
4. The app will transcribe and sync lyrics automatically

### From Metadata
When you load a music file, the app automatically checks for:
- **SYLT** (synchronized lyrics in metadata) - highest priority
- **USLT** (unsynchronized lyrics in metadata)
- **ID3 tags** embedded lyrics

### From External Files
The app checks for matching .lrc, .srt, or .ass files next to the audio file.
You can also import manually via **Lyrics > Import .lrc/.srt/.ass**.

### Edit Timing
- **Shift Earlier/Later** - Adjust all lyrics timing by 0.1s increments
- **Reset Sync** - Reset all timing adjustments
- **Manual Edit** - Edit lyrics text directly in the editor

### Sync Quality Indicator
- **Excellent** - Word-level timestamps, high confidence
- **Good** - Line-level timestamps
- **Needs Review** - Some timing issues detected
- **Failed** - Sync failed, manual correction needed

## Using Metadata Lyrics

When a music file is loaded, the app automatically reads:
- **ID3 Tags** (MP3) - title, artist, album, year, genre, cover art
- **USLT** - unsynchronized lyrics
- **SYLT** - synchronized lyrics with timestamps
- **FLAC/M4A/WAV** metadata

The metadata panel shows all available information. If synchronized lyrics are found in metadata, they are used before AI generation.

## Karaoke Modes

20 karaoke display modes available:

| # | Mode | Description |
|---|------|-------------|
| 1 | Normal Lyrics | Static lyrics display |
| 2 | Line Highlight | Active line brighter, others dimmed |
| 3 | Word Highlight | Per-word highlight following vocals |
| 4 | Smooth Sweep | Smooth left-to-right highlight sweep |
| 5 | Bounce Mode | Active word bounces with beat |
| 6 | Neon Glow | Modern neon glow effect |
| 7 | Gradient Flow | Moving gradient following timing |
| 8 | Beat Reactive | Scale and glow following beat/drop |
| 9 | Typewriter | Typing effect per character/word |
| 10 | Slide Reveal | Slide reveal left-right/top-bottom |
| 11 | Wave | Smooth wave motion |
| 12 | Pulse | Pulse following vocals |
| 13 | Cinematic | Minimalist cinematic style |
| 14 | Split Lyrics | For duet/multi vocalist |
| 15 | Vertical | For Shorts/TikTok/Reels |
| 16 | Floating | Smooth floating lyrics |
| 17 | Subtitle Pro | Clean professional subtitle style |
| 18 | Dynamic Zoom | Active word with smooth zoom |
| 19 | Multi Color | Colors change with beat/spectrum |
| 20 | Fire/Particle | Particle effects (auto-disabled in Low Spec) |

### Karaoke Presets
- EDM Neon Karaoke
- TikTok Modern Lyrics
- Anime Karaoke
- Cyberpunk Glow
- LoFi Chill Lyrics
- Minimal Subtitle
- Concert Style
- Night Drive Neon
- Cinematic Clean
- Bass Reactive Lyrics

## Using Logo/Watermark

1. Go to **Logo** tab
2. Check **Enable Logo/Watermark**
3. Click **Select Logo** (PNG with transparency or JPG)
4. Configure position, size, opacity
5. Choose animation (Fade In, Fade Out, Pulse, Zoom)

## Using CTA Animations

1. Go to **CTA** tab
2. Check **Enable CTA Animation**
3. Choose CTA type: Subscribe, Like, Share, Comment, Follow, Custom
4. Set timing: Start, Middle, End, or Custom Timestamp
5. Choose preset or upload custom animation (GIF, WEBM, MP4, MOV, PNG)
6. Optional: Enable Chroma Key for green screen removal

## Batch Render

1. Go to **Batch** tab
2. Select **Music Folder** (containing MP3/WAV/M4A/FLAC files)
3. Select **Background Folder** (containing images/videos)
4. Choose background mode:
   - **Random** - Random background for each song
   - **Sequential** - Backgrounds assigned in order
   - **Match by Filename** - Match by same filename (e.g., song1.mp3 + song1.jpg)
5. Configure auto-lyrics and sync options
6. Click **Scan Files** to preview jobs
7. Click **Start Batch Render**

Batch mode automatically:
- Generates lyrics for each song
- Checks metadata lyrics first
- Caches audio analysis for speed
- Saves a CSV report in the logs folder

## Low Spec Mode

For older/slower computers:

1. Go to **Render** tab
2. Set Quality Mode to **Low Spec**

Low Spec mode settings:
- Preview: 10 seconds at 480p
- Render: 720p resolution
- FPS: 24
- Lightweight spectrum (no glow/reflection)
- Particle effects disabled
- FFmpeg preset: ultrafast
- Cached audio analysis
- Low memory mode

## Spectrum Styles

- **Bar Spectrum** - Classic vertical bars (default, positioned at bottom)
- **Circular Spectrum** - Circular radial visualization
- **Waveform** - Oscilloscope-style waveform
- **Neon Spectrum** - Neon-glowing bar spectrum
- **Modern Visualizer** - Segmented modern style
- **Smooth Reactive** - Smooth filled reactive visualization

### Spectrum Presets
- Neon Rainbow, Cyberpunk, Ocean Blue, Sunset Glow
- Fire Beat, Purple Night, Minimal Clean, Colorful Pop

## Output Formats

### Aspect Ratios
- 16:9 YouTube (1920x1080)
- 9:16 TikTok/Reels/Shorts (1080x1920)
- 1:1 Instagram Square (1080x1080)
- 4:5 Instagram Feed (1080x1350)
- Custom

### Resolutions
- 360p, 480p, 720p HD, 1080p Full HD, 1440p 2K, 2160p 4K

## Troubleshooting

### FFmpeg not found
- Install FFmpeg and add it to your system PATH
- On Windows: `winget install --id Gyan.FFmpeg`
- On Linux: `sudo apt install ffmpeg`

### PyQt6 import error
```bash
pip install PyQt6
```

### Whisper model download fails
- Check your internet connection
- Try a smaller model (Faster-Whisper Small)
- Check disk space for model downloads (~1-3 GB)

### GPU not detected
- Install CUDA toolkit and PyTorch with CUDA support:
  ```bash
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```
- The app automatically falls back to CPU if GPU is not available

### Video rendering is slow
- Use Low Spec mode (Render tab > Quality: Low Spec)
- Reduce resolution (720p instead of 1080p)
- Lower FPS (24 instead of 30/60)
- Close other applications to free memory

### Lyrics not syncing correctly
- Try Re-Sync button in the Karaoke tab
- Use Shift Earlier/Later buttons to adjust timing
- Try a different Whisper model (WhisperX for best accuracy)
- Import .lrc file if available

### Application freezes
- Check the Log tab for errors
- The app uses background threads for heavy processing
- If stuck, check Task Manager for FFmpeg processes

## Project Structure

```
music-spectrum-lyrics-studio/
├── main.py                  # Entry point
├── setup.bat                # Windows setup
├── run.bat                  # Windows launcher
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── app/
│   ├── core/config.py       # Configuration and constants
│   ├── utils/helpers.py     # Utility functions
│   ├── audio/analyzer.py    # Audio analysis engine
│   ├── lyrics/
│   │   ├── metadata_lyrics_extractor.py  # Metadata extraction
│   │   ├── whisper_engine.py             # AI transcription
│   │   ├── karaoke_engine.py             # Karaoke timing
│   │   ├── karaoke_effects.py            # Visual effects
│   │   └── karaoke_presets.py            # Preset management
│   ├── visual/
│   │   ├── spectrum_renderer.py     # Spectrum visualization
│   │   ├── position_manager.py      # Element positioning
│   │   ├── logo_manager.py          # Logo overlay
│   │   └── cta_animation_manager.py # CTA animations
│   ├── render/
│   │   ├── video_renderer.py        # Video composition
│   │   ├── batch_folder_renderer.py # Batch rendering
│   │   └── render_queue.py          # Render queue
│   ├── project/
│   │   ├── project_manager.py       # Project save/load
│   │   └── batch_project_manager.py # Batch configurations
│   └── ui/
│       ├── main_window.py           # Main window
│       ├── styles.py                # Dark theme
│       └── components/              # UI panels
├── assets/                  # App assets
├── presets/                 # Preset JSON files
├── projects/                # Saved projects
├── output/                  # Rendered videos
├── temp/                    # Temporary files
├── cache/                   # Analysis cache
├── logs/                    # Log files
└── config/                  # Configuration files
```

## License

This project is provided as-is for personal and educational use.
