import type {
  VisualizerGenreId,
  VisualizerPreset,
  VisualizerStyleId,
} from "@/types/studio";

interface GenreInfo {
  id: VisualizerGenreId;
  label: string;
  region: string;
}

export const VISUALIZER_GENRES: GenreInfo[] = [
  { id: "edm", label: "EDM / Electronic", region: "Global" },
  { id: "pop", label: "Pop", region: "Global / USA / UK" },
  { id: "rock", label: "Rock", region: "USA / UK / Global" },
  { id: "metal", label: "Metal", region: "Europe / USA" },
  { id: "hiphop", label: "Hip-Hop / R&B", region: "USA / Global" },
  { id: "trap", label: "Trap / Drill", region: "USA / UK" },
  { id: "lofi", label: "Lo-Fi / Chill", region: "Japan / Global" },
  { id: "jazz", label: "Jazz / Soul", region: "USA / Brazil" },
  { id: "classical", label: "Classical / Orchestral", region: "Europe" },
  { id: "world", label: "World / Folk", region: "Africa / Asia / Latam" },
  { id: "kpop", label: "K-Pop / J-Pop", region: "Korea / Japan" },
  { id: "latin", label: "Latin / Reggaeton", region: "Latin America" },
];

const STYLES: VisualizerStyleId[] = [
  "bars",
  "bars-mirror",
  "circle-bars",
  "circle-wave",
  "wave",
  "wave-area",
  "rings",
  "dots",
  "ribbon",
  "particles",
  "spiral",
  "polygon",
  "stairs",
  "blocks",
];

interface GenrePalette {
  presets: Array<{
    name: string;
    style: VisualizerStyleId;
    colorA: string;
    colorB: string;
    glow: number;
  }>;
}

const GENRE_PALETTES: Record<VisualizerGenreId, GenrePalette> = {
  edm: {
    presets: [
      { name: "Neon Pulse", style: "bars", colorA: "#7c5cff", colorB: "#21d4fd", glow: 0.9 },
      { name: "Laser Mirror", style: "bars-mirror", colorA: "#ff2bd6", colorB: "#21d4fd", glow: 1 },
      { name: "Rave Circle", style: "circle-bars", colorA: "#21d4fd", colorB: "#7c5cff", glow: 0.85 },
      { name: "Sound Rings", style: "rings", colorA: "#ff5bf0", colorB: "#7c5cff", glow: 0.8 },
      { name: "Particle Drop", style: "particles", colorA: "#21d4fd", colorB: "#ffffff", glow: 0.7 },
      { name: "Energy Ribbon", style: "ribbon", colorA: "#ff007a", colorB: "#7c5cff", glow: 0.85 },
      { name: "Festival Spiral", style: "spiral", colorA: "#7c5cff", colorB: "#21d4fd", glow: 0.9 },
      { name: "Cyber Blocks", style: "blocks", colorA: "#1aff8c", colorB: "#21d4fd", glow: 0.8 },
    ],
  },
  pop: {
    presets: [
      { name: "Bubblegum Bars", style: "bars", colorA: "#ff77c6", colorB: "#ffc371", glow: 0.5 },
      { name: "Sunset Wave", style: "wave", colorA: "#ff6a88", colorB: "#ff9a8b", glow: 0.55 },
      { name: "Soft Mirror", style: "bars-mirror", colorA: "#ffc8dd", colorB: "#a2d2ff", glow: 0.5 },
      { name: "Hearts Circle", style: "circle-wave", colorA: "#ff6b9d", colorB: "#ffd3b6", glow: 0.6 },
      { name: "Glitter Dots", style: "dots", colorA: "#ffafcc", colorB: "#bde0fe", glow: 0.55 },
      { name: "Stage Stairs", style: "stairs", colorA: "#ff8a5b", colorB: "#ffc371", glow: 0.5 },
      { name: "Polygon Pop", style: "polygon", colorA: "#ff6b9d", colorB: "#7c5cff", glow: 0.5 },
    ],
  },
  rock: {
    presets: [
      { name: "Stadium Bars", style: "bars", colorA: "#ff4f4f", colorB: "#ffa64f", glow: 0.55 },
      { name: "Amp Mirror", style: "bars-mirror", colorA: "#ff3838", colorB: "#ffd166", glow: 0.55 },
      { name: "Crowd Wave", style: "wave-area", colorA: "#e63946", colorB: "#f1faee", glow: 0.5 },
      { name: "Guitar Rings", style: "rings", colorA: "#f4a261", colorB: "#e76f51", glow: 0.55 },
      { name: "Drum Polygon", style: "polygon", colorA: "#d62828", colorB: "#f77f00", glow: 0.55 },
      { name: "Riff Blocks", style: "blocks", colorA: "#e76f51", colorB: "#2a9d8f", glow: 0.5 },
    ],
  },
  metal: {
    presets: [
      { name: "Inferno Bars", style: "bars", colorA: "#ff3d00", colorB: "#ffab00", glow: 1 },
      { name: "Lava Mirror", style: "bars-mirror", colorA: "#dd2c00", colorB: "#ff6f00", glow: 1 },
      { name: "Skull Spiral", style: "spiral", colorA: "#ff1744", colorB: "#212121", glow: 0.95 },
      { name: "Iron Polygon", style: "polygon", colorA: "#9e9e9e", colorB: "#ff5252", glow: 0.9 },
      { name: "Thunder Wave", style: "wave", colorA: "#ff5252", colorB: "#ffd740", glow: 1 },
    ],
  },
  hiphop: {
    presets: [
      { name: "Gold Bars", style: "bars", colorA: "#ffd700", colorB: "#ff8a00", glow: 0.7 },
      { name: "808 Mirror", style: "bars-mirror", colorA: "#ffd166", colorB: "#ef476f", glow: 0.7 },
      { name: "Vinyl Rings", style: "rings", colorA: "#ffd700", colorB: "#000000", glow: 0.8 },
      { name: "Boombox Blocks", style: "blocks", colorA: "#ffaa00", colorB: "#ff4d00", glow: 0.7 },
      { name: "Bass Wave", style: "wave-area", colorA: "#ffae00", colorB: "#7c4dff", glow: 0.7 },
      { name: "Soul Particles", style: "particles", colorA: "#ffd54f", colorB: "#ff8a65", glow: 0.65 },
    ],
  },
  trap: {
    presets: [
      { name: "Trap Bars", style: "bars", colorA: "#a020f0", colorB: "#00ffe1", glow: 0.9 },
      { name: "Drip Mirror", style: "bars-mirror", colorA: "#8a2be2", colorB: "#00ffff", glow: 0.9 },
      { name: "Hype Circle", style: "circle-bars", colorA: "#bf00ff", colorB: "#00ffaa", glow: 0.9 },
      { name: "Hi-Hat Dots", style: "dots", colorA: "#ff00aa", colorB: "#00ffff", glow: 0.9 },
      { name: "Ride Ribbon", style: "ribbon", colorA: "#bf00ff", colorB: "#00aaff", glow: 0.9 },
    ],
  },
  lofi: {
    presets: [
      { name: "Lo-Fi Bars", style: "bars", colorA: "#f4d1ae", colorB: "#b08968", glow: 0.3 },
      { name: "Cozy Wave", style: "wave", colorA: "#e6ccb2", colorB: "#9c6644", glow: 0.25 },
      { name: "Study Dots", style: "dots", colorA: "#cdb4db", colorB: "#ffc8dd", glow: 0.25 },
      { name: "Tape Rings", style: "rings", colorA: "#a98467", colorB: "#dcc6a9", glow: 0.25 },
      { name: "Chill Ribbon", style: "ribbon", colorA: "#bfa18a", colorB: "#e5b9a4", glow: 0.3 },
    ],
  },
  jazz: {
    presets: [
      { name: "Smoke Bars", style: "bars", colorA: "#d4af37", colorB: "#5e2c04", glow: 0.4 },
      { name: "Sax Wave", style: "wave", colorA: "#c08552", colorB: "#3a1c0a", glow: 0.4 },
      { name: "Lounge Rings", style: "rings", colorA: "#deb841", colorB: "#7d0a0a", glow: 0.4 },
      { name: "Brass Polygon", style: "polygon", colorA: "#ffb703", colorB: "#fb8500", glow: 0.45 },
    ],
  },
  classical: {
    presets: [
      { name: "Opera Wave", style: "wave-area", colorA: "#d4af37", colorB: "#1a1a40", glow: 0.4 },
      { name: "Symphony Circle", style: "circle-wave", colorA: "#e0c097", colorB: "#5c3317", glow: 0.4 },
      { name: "Concerto Rings", style: "rings", colorA: "#f4f1de", colorB: "#3d405b", glow: 0.4 },
      { name: "Marble Bars", style: "bars", colorA: "#f3e9d2", colorB: "#7a6c5d", glow: 0.3 },
    ],
  },
  world: {
    presets: [
      { name: "Savanna Bars", style: "bars", colorA: "#ff8c42", colorB: "#6a040f", glow: 0.5 },
      { name: "Bamboo Wave", style: "wave", colorA: "#8ac926", colorB: "#1982c4", glow: 0.45 },
      { name: "Sari Circle", style: "circle-bars", colorA: "#ff595e", colorB: "#ffca3a", glow: 0.55 },
      { name: "Maraca Dots", style: "dots", colorA: "#a4c93f", colorB: "#ff595e", glow: 0.5 },
      { name: "Sahara Polygon", style: "polygon", colorA: "#e36414", colorB: "#9a031e", glow: 0.55 },
    ],
  },
  kpop: {
    presets: [
      { name: "Idol Bars", style: "bars", colorA: "#ff77e9", colorB: "#a2d2ff", glow: 0.8 },
      { name: "Light Stick Mirror", style: "bars-mirror", colorA: "#ff8fcf", colorB: "#9bf6ff", glow: 0.85 },
      { name: "Bias Wave", style: "wave", colorA: "#ffb7ff", colorB: "#bdb2ff", glow: 0.8 },
      { name: "Dance Spiral", style: "spiral", colorA: "#ff70a6", colorB: "#70d6ff", glow: 0.85 },
      { name: "Fanchant Ribbon", style: "ribbon", colorA: "#ff9cee", colorB: "#caffbf", glow: 0.8 },
    ],
  },
  latin: {
    presets: [
      { name: "Salsa Bars", style: "bars", colorA: "#ef233c", colorB: "#ffba08", glow: 0.7 },
      { name: "Reggaeton Mirror", style: "bars-mirror", colorA: "#ff006e", colorB: "#ffbe0b", glow: 0.75 },
      { name: "Bachata Circle", style: "circle-bars", colorA: "#fb5607", colorB: "#3a86ff", glow: 0.7 },
      { name: "Cumbia Wave", style: "wave", colorA: "#fb5607", colorB: "#ff006e", glow: 0.7 },
      { name: "Carnaval Particles", style: "particles", colorA: "#ffbe0b", colorB: "#ff006e", glow: 0.75 },
    ],
  },
};

export const VISUALIZER_PRESETS: VisualizerPreset[] = (
  Object.entries(GENRE_PALETTES) as [VisualizerGenreId, GenrePalette][]
).flatMap(([genre, group]) =>
  group.presets.map((p, idx) => ({
    id: `${genre}-${idx}`,
    genre,
    name: p.name,
    style: p.style,
    colorA: p.colorA,
    colorB: p.colorB,
    glow: p.glow,
    smoothing: 0.78,
    bars: 64,
    thickness: 4,
  })),
);

export const VISUALIZER_STYLE_LABELS: Record<VisualizerStyleId, string> = {
  bars: "Bars",
  "bars-mirror": "Mirror Bars",
  "circle-bars": "Circle Bars",
  "circle-wave": "Circle Wave",
  wave: "Wave",
  "wave-area": "Wave Filled",
  rings: "Rings",
  dots: "Dots",
  ribbon: "Ribbon",
  particles: "Particles",
  spiral: "Spiral",
  polygon: "Polygon",
  stairs: "Stairs",
  blocks: "Blocks",
};

export const ALL_STYLES = STYLES;
