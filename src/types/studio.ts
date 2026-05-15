export type AspectRatioId =
  | "16:9"
  | "9:16"
  | "1:1"
  | "4:5"
  | "4:3"
  | "3:4"
  | "21:9";

export interface AspectRatio {
  id: AspectRatioId;
  label: string;
  w: number;
  h: number;
}

export interface AudioTrack {
  id: string;
  name: string;
  file: File;
  url: string;
  duration: number;
}

export type LayerType =
  | "background"
  | "visualizer"
  | "image"
  | "text"
  | "lyrics"
  | "effect";

export interface BaseLayer {
  id: string;
  type: LayerType;
  name: string;
  visible: boolean;
  locked: boolean;
  /** Position is in normalized canvas coords (0..1) */
  x: number;
  y: number;
  /** Size in normalized canvas coords (0..1) */
  width: number;
  height: number;
  rotation: number;
  opacity: number;
}

export type ImageShape = "original" | "circle" | "rounded";
export type ImageRotateMode = "none" | "cw" | "ccw";

export interface ImageLayer extends BaseLayer {
  type: "image";
  src: string; // object URL
  fileName: string;
  shape: ImageShape;
  rotateMode: ImageRotateMode;
  rotateSpeed: number; // deg/sec
  /** 0..1 transparency multiplier (in addition to opacity) */
  transparency: number;
  beatZoom: boolean;
  beatZoomAmount: number; // 0..1
  beatDivision: 1 | 2 | 4 | 8; // pulse subdivision
  outlineWidth: number;
  outlineColor: string;
}

export type TextStyleId = "normal" | "italic" | "bold" | "boldItalic";

export interface TextLayer extends BaseLayer {
  type: "text";
  text: string;
  fontFamily: string;
  fontSize: number; // px in 1080p canvas
  fontWeight: 300 | 400 | 500 | 600 | 700 | 800;
  italic: boolean;
  color: string;
  strokeColor: string;
  strokeWidth: number;
  shadow: boolean;
  shadowColor: string;
  letterSpacing: number;
  align: "left" | "center" | "right";
  beatZoom: boolean;
  beatZoomAmount: number;
}

export type LyricAnimation =
  | "fade"
  | "typewriter"
  | "slide-up"
  | "scale-pop"
  | "neon-glow"
  | "bounce"
  | "karaoke";

export interface LyricLine {
  time: number; // seconds
  duration: number; // seconds
  text: string;
}

export interface LyricsLayer extends BaseLayer {
  type: "lyrics";
  lines: LyricLine[];
  fontFamily: string;
  fontSize: number;
  fontWeight: 300 | 400 | 500 | 600 | 700 | 800;
  italic: boolean;
  color: string;
  highlightColor: string;
  strokeColor: string;
  strokeWidth: number;
  shadow: boolean;
  align: "left" | "center" | "right";
  animation: LyricAnimation;
  style: "plain" | "neon" | "outline" | "gradient" | "chrome";
  beatZoom: boolean;
  beatZoomAmount: number;
}

export type VisualizerStyleId =
  | "bars"
  | "bars-mirror"
  | "circle-bars"
  | "circle-wave"
  | "wave"
  | "wave-area"
  | "rings"
  | "dots"
  | "ribbon"
  | "particles"
  | "spiral"
  | "polygon"
  | "stairs"
  | "blocks";

export type VisualizerGenreId =
  | "edm"
  | "pop"
  | "rock"
  | "hiphop"
  | "lofi"
  | "jazz"
  | "classical"
  | "world"
  | "metal"
  | "trap"
  | "kpop"
  | "latin";

export interface VisualizerPreset {
  id: string; // unique
  genre: VisualizerGenreId;
  name: string;
  style: VisualizerStyleId;
  colorA: string;
  colorB: string;
  glow: number; // 0..1
  smoothing: number; // 0..1
  bars?: number;
  thickness?: number;
}

export interface VisualizerLayer extends BaseLayer {
  type: "visualizer";
  presetId: string;
  // overrides (so user can tweak after picking preset)
  colorA?: string;
  colorB?: string;
  glow?: number;
  smoothing?: number;
  bars?: number;
  thickness?: number;
  mirror?: boolean;
}

export type BackgroundKind = "image" | "video";

export interface BackgroundItem {
  id: string;
  kind: BackgroundKind;
  src: string; // object URL
  fileName: string;
}

export type BackgroundFit = "cover" | "contain" | "fill";

export interface BackgroundLayer extends BaseLayer {
  type: "background";
  items: BackgroundItem[];
  intervalSec: number; // time between automatic switches
  crossfadeSec: number;
  blur: number; // 0..40
  brightness: number; // 0..2
  fit: BackgroundFit;
}

export type EffectKind =
  | "rain"
  | "heavy-rain"
  | "snow"
  | "blizzard"
  | "smoke"
  | "fog"
  | "fireflies"
  | "bubbles"
  | "leaves"
  | "petals"
  | "stars"
  | "shooting-stars"
  | "embers"
  | "confetti"
  | "music-notes"
  | "hearts"
  | "dust"
  | "lightning"
  | "sparkles"
  | "fireworks"
  | "neon-grid"
  | "rays"
  | "glitch";

export type EffectGenreId =
  | "weather"
  | "nature"
  | "magic"
  | "party"
  | "music"
  | "scifi";

export interface EffectPreset {
  id: string;
  genre: EffectGenreId;
  name: string;
  kind: EffectKind;
}

export interface EffectLayer extends BaseLayer {
  type: "effect";
  presetId: string;
  intensity: number; // 0..1
  color?: string;
  speed: number;
  beatReactive: boolean;
}

export type Layer =
  | ImageLayer
  | TextLayer
  | LyricsLayer
  | VisualizerLayer
  | BackgroundLayer
  | EffectLayer;

export type MenuId =
  | "audio"
  | "image"
  | "visualizer"
  | "background"
  | "effects"
  | "text"
  | "lyrics"
  | "export";

export interface ExportSettings {
  width: number;
  height: number;
  fps: 24 | 30 | 60;
  bitrateMbps: number;
  format: "webm" | "mp4";
}

export interface GroqKey {
  id: string;
  name: string;
  key: string;
}

export interface AudioState {
  tracks: AudioTrack[];
  currentTrackId: string | null;
  playing: boolean;
  currentTime: number;
  beatSensitivity: number; // 0..1
  beatBpm: number; // detected BPM, 0 = unknown
  loopPlaylist: boolean;
}
