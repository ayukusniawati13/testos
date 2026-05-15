# Music Spectrum & Lyrics Video Studio

A browser-based studio for creating **music visualizer videos** with spectrum analyzers, beat-reactive animations, lyric overlays and a precise drag-and-drop preview. Everything runs in the browser — no server required for the core editor.

## Layout

Three panels, designed for fast iteration:

- **Left — Layers**: every element you add (image, text, lyrics, visualizer, background, effect) shows up here. Reorder, toggle visibility/lock, or delete from a single place.
- **Center — Preview**: a precise WYSIWYG canvas. Every layer can be dragged and resized with snap-handles, and pixel coordinates match the export exactly.
- **Right — Icon menu**: 8 menus accessible from icons, each opening a contextual sidebar.

## The 8 menus

| Menu | Features |
| --- | --- |
| **Audio** | Aspect ratio picker (16:9, 9:16, 1:1, 4:5, 4:3, 3:4, 21:9), multi-track upload, playlist with auto-advance + loop, Web Audio playback, **beat sensitivity** and live BPM readout. |
| **Image** | Multi-image upload with **per-image settings**: shape (original / rounded / circle), static rotation, animated rotation (CW/CCW with speed), transparency, beat zoom (with 1x/2x/4x/8x subdivision), outline width + color. |
| **Visualizer** | 60+ spectrum presets organized by **12 global genres** (EDM, Pop, Rock, Metal, Hip-Hop, Trap, Lo-Fi, Jazz, Classical, World, K-Pop, Latin) across 14 rendering styles (bars, mirror bars, circle bars, circle wave, wave, wave area, rings, dots, ribbon, particles, spiral, polygon, stairs, blocks). |
| **Background** | Multi image/video upload with smooth **timed crossfade**, blur, brightness, fit modes (cover/contain/fill). |
| **Effects** | 25+ particle effects in 6 genres: weather (rain, heavy rain, snow, blizzard, fog, lightning), nature (fireflies, bubbles, leaves, petals, dust, embers), magic (sparkles, stars, shooting stars, smoke, hearts), party (confetti, fireworks, rays), music (notes, beat reactive), sci-fi (neon grid, glitch). Each is beat-reactive. |
| **Text** | Multiple text layers, 26 Google fonts, weight/italic/alignment, color/outline/shadow, **beat zoom**. |
| **Lyrics** | Multiple Groq API keys, AI lyric transcription via Groq Whisper, manual `[m:ss]` editor, 7 animations (fade, typewriter, slide-up, scale-pop, neon-glow, bounce, **karaoke**), 5 styles (plain, neon, outline, gradient, chrome), **beat zoom**. |
| **Export** | Resolution presets up to 4K, 24/30/60 fps, bitrate control, WebM or MP4 (browser-permitting). Exports via `MediaRecorder` capturing the live preview + audio. |

## Beat detection

A custom analyzer (FFT 2048, smoothing 0.78) computes bass-band onset detection against an adaptive threshold derived from a 1-second history. Beats drive the `pulse` value that powers every "beat zoom" / "beat reactive" feature. Detected BPM is shown live in the Audio menu.

## Development

```bash
npm install
npm run dev      # vite dev server on http://localhost:5173
npm run build    # type-check + production build
npm run lint     # eslint
```

## Tech

React 19, TypeScript, Vite, Tailwind v4, Zustand, Lucide icons, Web Audio API, Canvas 2D, MediaRecorder, Groq API.
