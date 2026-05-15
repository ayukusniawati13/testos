import type { EffectGenreId, EffectKind, EffectPreset } from "@/types/studio";

interface GenreInfo {
  id: EffectGenreId;
  label: string;
}

export const EFFECT_GENRES: GenreInfo[] = [
  { id: "weather", label: "Weather" },
  { id: "nature", label: "Nature" },
  { id: "magic", label: "Magic / Fantasy" },
  { id: "party", label: "Party / Stage" },
  { id: "music", label: "Music" },
  { id: "scifi", label: "Sci-Fi / Cyber" },
];

interface Entry {
  name: string;
  kind: EffectKind;
}

const GROUPS: Record<EffectGenreId, Entry[]> = {
  weather: [
    { name: "Light Rain", kind: "rain" },
    { name: "Heavy Rain", kind: "heavy-rain" },
    { name: "Snowfall", kind: "snow" },
    { name: "Blizzard", kind: "blizzard" },
    { name: "Fog", kind: "fog" },
    { name: "Lightning Flash", kind: "lightning" },
  ],
  nature: [
    { name: "Fireflies", kind: "fireflies" },
    { name: "Bubbles", kind: "bubbles" },
    { name: "Falling Leaves", kind: "leaves" },
    { name: "Cherry Petals", kind: "petals" },
    { name: "Dust Motes", kind: "dust" },
    { name: "Embers", kind: "embers" },
  ],
  magic: [
    { name: "Sparkles", kind: "sparkles" },
    { name: "Stars", kind: "stars" },
    { name: "Shooting Stars", kind: "shooting-stars" },
    { name: "Mystic Smoke", kind: "smoke" },
    { name: "Floating Hearts", kind: "hearts" },
  ],
  party: [
    { name: "Confetti", kind: "confetti" },
    { name: "Fireworks", kind: "fireworks" },
    { name: "Stage Sparks", kind: "embers" },
    { name: "Light Rays", kind: "rays" },
  ],
  music: [
    { name: "Music Notes", kind: "music-notes" },
    { name: "Pulse Sparks", kind: "sparkles" },
    { name: "Beat Particles", kind: "dust" },
  ],
  scifi: [
    { name: "Neon Grid", kind: "neon-grid" },
    { name: "Glitch Bits", kind: "glitch" },
    { name: "Hologram Dust", kind: "dust" },
    { name: "Cyber Sparks", kind: "embers" },
  ],
};

export const EFFECT_PRESETS: EffectPreset[] = (
  Object.entries(GROUPS) as [EffectGenreId, Entry[]][]
).flatMap(([genre, list]) =>
  list.map((e, idx) => ({
    id: `${genre}-${e.kind}-${idx}`,
    genre,
    name: e.name,
    kind: e.kind,
  })),
);
