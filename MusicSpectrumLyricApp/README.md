# Music Spectrum Lyric Video Maker

Aplikasi desktop profesional untuk membuat video musik dengan spectrum audio visualizer dan lirik otomatis berbasis file .LRC.

Cocok untuk membuat video musik siap upload ke **YouTube**, **TikTok**, dan **Instagram**.

---

## Fitur Utama

- **12 gaya spectrum/visualizer**: Bar Modern, Circular, Waveform, Radial Pulse, Neon Equalizer, Smooth Blob, Particle, Mirror Wave, Minimal Bars, Cinematic Glow, Audio Ring, Liquid Wave
- **Sinkronisasi lirik .LRC**: Lirik muncul sesuai timestamp dengan transisi fade in/out yang smooth
- **Background kustom**: Mendukung gambar (JPG, PNG, WebP) dan video (MP4, MOV, MKV)
- **Logo overlay**: Posisi, ukuran, opacity, dan margin bisa diatur
- **Mode batch render**: Render banyak lagu sekaligus dengan matching otomatis
- **UI modern dark mode**: Tampilan profesional dan mudah digunakan
- **Auto-install FFmpeg**: Download dan install FFmpeg langsung dari aplikasi
- **Resolusi fleksibel**: 1920x1080, 1080x1920 (TikTok), 1280x720
- **Output MP4 H.264 + AAC**: Siap upload ke platform manapun

---

## Persyaratan Sistem

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.10 atau lebih baru
- **FFmpeg**: Akan di-download otomatis oleh aplikasi jika belum ada
- **RAM**: Minimal 4 GB (8 GB disarankan)
- **Disk**: Minimal 500 MB ruang kosong

---

## Cara Install

### 1. Install Python

Download dan install Python dari [python.org](https://www.python.org/downloads/).

> **Penting**: Centang opsi **"Add Python to PATH"** saat instalasi.

### 2. Jalankan Setup

```
Double-click setup.bat
```

Script ini akan:
- Mengecek instalasi Python
- Membuat virtual environment
- Menginstall semua dependensi
- Mengecek ketersediaan FFmpeg

### 3. Jalankan Aplikasi

```
Double-click run.bat
```

---

## Cara Menggunakan

### Mode Single Render

1. Klik **"Browse"** di bagian **Music** untuk memilih file musik
2. Klik **"Browse"** di bagian **Lyrics** untuk memilih file .LRC
3. (Opsional) Pilih background gambar atau video
4. (Opsional) Pilih logo
5. Atur pengaturan di panel kanan (spectrum style, font, warna, dll)
6. Klik **"Update Preview"** untuk melihat preview
7. Klik **"Render Video"** untuk memulai render

### Mode Batch Render

1. Pindah ke tab **"Batch Render"**
2. Pilih folder musik, folder lirik, folder background, dan folder output
3. Pilih mode background (Match by Filename, Sequential, Random)
4. Klik **"Scan & Match Files"** untuk mencocokkan file
5. Review tabel matching
6. Klik **"Start Batch Render"**

### Matching File Batch

Aplikasi mencocokkan file berdasarkan nama:

```
Music:      We Drifted Without Knowing.mp3
Lyrics:     We Drifted Without Knowing.lrc
Background: We Drifted Without Knowing.jpg
```

---

## Format File .LRC

File .LRC menggunakan format timestamp seperti ini:

```
[00:17.50]We used to talk until the sunrise came
[00:21.20]Now we barely say each other's names
[00:24.80]No fight, no storm, no shattered scene
[00:28.40]Just silence slowly in between
[00:32.00]We drifted without knowing
[00:35.60]Like seasons changing without showing
[00:39.20]The love we had just slipped away
[00:42.80]And I still think about it every day

[01:00.00]Sometimes I wonder if you feel it too
[01:03.60]The empty space where I once stood with you
[01:07.20]We never said the words we meant to say
[01:10.80]We just let it fade away
```

**Aturan timestamp:**
- Format: `[mm:ss.xx]` (menit:detik.milidetik)
- Lirik muncul mulai dari timestamp pertama
- Sebelum timestamp pertama, layar lirik kosong
- Lirik berganti sesuai timestamp berikutnya
- Jeda panjang antar lirik akan menghasilkan fade out otomatis

---

## Gaya Spectrum

| # | Nama | Deskripsi |
|---|------|-----------|
| 1 | Bar Spectrum Modern | Bar vertikal dengan gradient dan rounded corners |
| 2 | Circular Spectrum | Spectrum melingkar di tengah layar |
| 3 | Waveform Line | Gelombang audio sinusoidal |
| 4 | Radial Pulse | Cincin berdenyut sesuai beat |
| 5 | Neon Equalizer | Bar tersegmentasi gaya neon |
| 6 | Smooth Blob Spectrum | Blob organik yang bergerak sesuai audio |
| 7 | Particle Spectrum | Partikel yang responsif terhadap beat |
| 8 | Mirror Wave | Gelombang cermin atas-bawah |
| 9 | Minimal Thin Bars | Bar tipis minimalis |
| 10 | Cinematic Glow Spectrum | Bar dengan efek glow sinematik |
| 11 | Audio Ring Spectrum | Cincin berlapis responsif audio |
| 12 | Liquid Wave Spectrum | Gelombang cair berlapis |

---

## Pengaturan yang Tersedia

### Video
- Resolusi: 1920x1080, 1080x1920, 1280x720
- FPS: 30 atau 60
- Bitrate: 4M - 15M

### Spectrum
- 12 gaya visualizer
- Sensitivity, height, position
- Opacity, glow, blur
- 2 warna gradient
- Smoothing

### Lirik
- Font family, size
- Warna teks, shadow, stroke, glow
- Posisi dan alignment
- Fade duration
- Opsi tampilkan baris berikutnya

### Logo
- Posisi: 5 pilihan
- Ukuran, opacity, margin

---

## Struktur Proyek

```
MusicSpectrumLyricApp/
├── app/
│   ├── main.py                 # Entry point
│   ├── ui/
│   │   ├── main_window.py      # Main window
│   │   ├── batch_panel.py      # Batch render panel
│   │   ├── settings_panel.py   # Settings panel
│   │   └── preview_panel.py    # Preview panel
│   ├── core/
│   │   ├── lrc_parser.py       # LRC file parser
│   │   ├── audio_analyzer.py   # Audio spectrum analysis
│   │   ├── spectrum_engine.py  # Spectrum visualizer engine
│   │   ├── lyric_renderer.py   # Lyric text renderer
│   │   ├── video_renderer.py   # Video composition & FFmpeg
│   │   ├── batch_manager.py    # Batch processing manager
│   │   └── ffmpeg_manager.py   # FFmpeg detection & install
│   └── styles/
│       ├── spectrum_styles.py  # Spectrum presets
│       └── themes.py           # Dark mode theme
├── output/                     # Rendered videos
├── temp/                       # Temporary files
├── requirements.txt
├── setup.bat
├── run.bat
└── README.md
```

---

## Troubleshooting

### FFmpeg Not Found
- Klik tombol **"Install FFmpeg Online"** di aplikasi
- Atau download manual dari [ffmpeg.org](https://ffmpeg.org/download.html)
- Extract ke folder `tools/ffmpeg/`

### Lirik Tidak Muncul
- Pastikan file .LRC memiliki format timestamp yang benar: `[mm:ss.xx]`
- Pastikan encoding file UTF-8

### Render Lambat
- Kurangi resolusi (gunakan 1280x720)
- Kurangi FPS ke 30
- Kurangi bitrate

### Error Saat Install
- Pastikan Python 3.10+ sudah terinstall
- Pastikan "Add Python to PATH" dicentang
- Jalankan `setup.bat` sebagai Administrator jika diperlukan

---

## Lisensi

Proyek ini dibuat untuk penggunaan pribadi dan edukasi.
