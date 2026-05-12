# Music Spectrum Studio

Aplikasi desktop Python untuk membuat **video musik dengan spectrum visualizer dan
lirik otomatis**. Sumber lirik di-generate langsung dari audio menggunakan
**Groq AI (Whisper-large-v3 / Whisper-large-v3-turbo)** dengan dukungan
**banyak API key dan rotasi otomatis** bila terkena rate-limit, plus pass
**AI text-correction** untuk memperbaiki kata yang tidak nyambung.

> Cocok untuk produksi konten YouTube, TikTok, Reels, lyric video.

---

## Fitur Utama

### Lirik otomatis (Groq Whisper)
- Transkripsi pakai `whisper-large-v3-turbo` / `whisper-large-v3` (pilih di UI).
- Word-level timestamps presisi (`timestamp_granularities=["word","segment"]`).
- **Multi API key** dengan **rotasi otomatis** saat 429 / kuota habis / 401.
  Tombol **Test Key** memverifikasi setiap key.
- **AI Correction** pakai Groq Chat (default `llama-3.3-70b-versatile`) untuk
  memperbaiki kata yang salah dengar dengan tetap menjaga jumlah baris & makna.
- Tombol **Generate Lirik** otomatis muncul setelah memilih musik.
- Export hasil ke **SRT** atau **LRC** dengan satu klik.

### Visualizer (19 gaya)
Bars Modern, Bars Rounded, Bars Mirror, Bars Gradient Glow, Equalizer Blocks,
Dotted Bars, Wave Smooth, Wave Mirror, Ribbon, Circular Bars, Circular Wave,
Pulse Ring, Radial Petals, Particles, Spectrogram Trail, Cinematic Glow,
Neon Equalizer, Liquid Wave, Minimal Line.

- Bar style **otomatis sejajar bagian bawah** video (posisi bisa diubah).
- Warna gradient dua-tone, smoothing, sensitivity, jumlah band.

### Lirik di video (8 gaya)
Centered Modern, Bottom Subtitle, Karaoke Highlight (highlight kata per kata),
Glow Large, Boxed Pill, Cinematic Top, Side Aligned, Typewriter.

- **Fade-in / fade-out** halus.
- **Jeda antar baris**: jika gap > X detik (kustom), baris sebelumnya hilang
  dulu, lalu baris berikutnya fade-in tepat di awal kata.
- **Pilihan font** otomatis di-scan dari sistem (Windows / macOS / Linux).

### Background
- Gambar atau video (mp4/mov/mkv).
- **Multi background** dengan **smooth crossfade** (durasi & cycle kustom).
- Blur, darken, fit cover / contain.

### Efek video
Sparkle (kelap-kelip), Glow / Bloom, Vignette, Beat-flash, Light leaks, Grain.

### Logo
- Pilih file gambar (PNG transparan disarankan).
- Opsi **bulatkan logo**.
- Posisi (anchor), ukuran (% lebar), margin X/Y, opacity.

### Batch mode
- Folder musik + folder background.
- Pencocokan: **urutan file**, **berdasarkan nama**, atau **acak**.
- Aktif/non-aktif via toggle.

### Preview & Render
- Pratinjau di sebelah kanan, slider waktu, refresh manual.
- Pengaturan render di bawah preview: resolusi sampai **2K (2560x1440)** +
  preset vertikal (TikTok/Reels), square (IG).
- Output MP4 H.264 + AAC siap upload.

### FFmpeg
- Status FFmpeg ditampilkan di header.
- Tombol **Install FFmpeg (online)** mengunduh binary dari `imageio-ffmpeg`
  secara otomatis bila system PATH tidak punya ffmpeg.

---

## Instalasi (Windows)

1. Install Python 3.10+ dari [python.org](https://www.python.org/downloads/)
   — centang **Add Python to PATH**.
2. Klik dua kali **`setup.bat`** untuk membuat virtualenv & install dependensi.
3. Klik **`run.bat`** untuk membuka aplikasi.

## Instalasi (Linux / macOS)

```bash
./setup.sh
./run.sh
```

## Cara pakai singkat

1. Tambahkan minimal satu Groq API key di panel atas (klik **+ Tambah API Key**,
   tempel key `gsk_...`, klik **Tes**). Tambahkan lebih dari satu agar otomatis
   rotasi bila limit.
2. Pilih file musik di tab **Musik & Lirik**.
3. Klik **Generate Lirik (Groq Whisper)** → hasil & timestamps muncul.
   Aktifkan **AI Correction** untuk membersihkan teks.
4. Atur **Spectrum**, **Lirik & Logo**, **Background**, **Efek** sesuai selera.
   Preview di kanan otomatis diperbarui.
5. Pilih resolusi (sampai **1440p / 2K**) di panel Render → klik **Render Video**.

Untuk **batch**, buka tab **Batch**, aktifkan toggle, pilih folder musik +
folder background dan strategi pencocokan, lalu **Render Video**.

## Struktur Project

```
MusicSpectrumStudio/
├── README.md
├── setup.bat / setup.sh
├── run.bat / run.sh
├── requirements.txt
├── pyproject.toml
└── app/
    ├── main.py               # Entry point
    ├── config.py             # Dataclass settings + persistence
    ├── constants.py
    ├── core/
    │   ├── ffmpeg_check.py   # Status + online install
    │   ├── groq_client.py    # Multi-key rotation
    │   ├── transcribe.py     # Whisper + AI correction
    │   ├── audio_spectrum.py # FFT bands + beat detection
    │   ├── render_pipeline.py
    │   ├── fonts.py
    │   └── batch.py
    ├── render/
    │   ├── spectrum_styles.py # 19 styles
    │   ├── lyrics_styles.py   # 8 styles + fade & gap handling
    │   ├── background.py      # multi-bg crossfade
    │   ├── effects.py         # sparkle / glow / vignette / ...
    │   ├── logo.py            # circular crop + anchor
    │   └── compositor.py
    ├── ui/                    # PySide6 dark theme + panels
    ├── workers/               # QThread workers (transcribe, render)
    └── utils/
```

## Catatan Bahasa

- Bahasa default untuk transkripsi: **otomatis**. Bisa di-paksa misalnya `id`
  (Indonesia) atau `en` (Inggris) di tab **Musik & Lirik**.

## Lisensi

MIT
