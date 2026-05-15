import { create } from "zustand";
import { nanoid } from "nanoid";
import { ASPECT_RATIOS, DEFAULT_ASPECT_RATIO } from "@/data/aspectRatios";
import { FONT_OPTIONS } from "@/data/fonts";
import { VISUALIZER_PRESETS } from "@/data/visualizers";
import { EFFECT_PRESETS } from "@/data/effects";
import type {
  AspectRatio,
  AudioTrack,
  BackgroundFit,
  BackgroundItem,
  BackgroundLayer,
  EffectLayer,
  ExportSettings,
  GroqKey,
  ImageLayer,
  Layer,
  LyricLine,
  LyricsLayer,
  MenuId,
  TextLayer,
  VisualizerLayer,
} from "@/types/studio";

interface StudioState {
  // panels
  activeMenu: MenuId | null;
  setActiveMenu: (id: MenuId | null) => void;

  // canvas
  aspect: AspectRatio;
  setAspect: (id: AspectRatio["id"]) => void;

  // audio
  tracks: AudioTrack[];
  currentTrackId: string | null;
  beatSensitivity: number;
  setBeatSensitivity: (v: number) => void;
  loopPlaylist: boolean;
  setLoopPlaylist: (v: boolean) => void;
  addTracks: (files: File[]) => Promise<void>;
  removeTrack: (id: string) => void;
  setCurrentTrack: (id: string | null) => void;
  reorderTracks: (from: number, to: number) => void;

  // layers
  layers: Layer[];
  selectedLayerId: string | null;
  setSelectedLayer: (id: string | null) => void;
  addImageLayer: (file: File) => Promise<void>;
  addTextLayer: () => void;
  addVisualizerLayer: (presetId: string) => void;
  addBackgroundLayer: () => void;
  addBackgroundItems: (layerId: string, files: File[]) => void;
  removeBackgroundItem: (layerId: string, itemId: string) => void;
  addEffectLayer: (presetId: string) => void;
  addLyricsLayer: () => void;
  removeLayer: (id: string) => void;
  toggleLayerVisible: (id: string) => void;
  toggleLayerLocked: (id: string) => void;
  moveLayer: (id: string, dir: -1 | 1) => void;
  updateLayer: <T extends Layer>(id: string, patch: Partial<T>) => void;

  // groq keys
  groqKeys: GroqKey[];
  addGroqKey: (name: string, key: string) => void;
  removeGroqKey: (id: string) => void;
  setLyrics: (layerId: string, lines: LyricLine[]) => void;

  // export
  exportSettings: ExportSettings;
  setExport: (patch: Partial<ExportSettings>) => void;

  // playback (synced from engine each frame)
  playing: boolean;
  setPlaying: (v: boolean) => void;
  currentTime: number;
  duration: number;
  setPlaybackTime: (t: number, d: number) => void;
  detectedBpm: number;
  setDetectedBpm: (v: number) => void;
}

const DEFAULT_FONT = FONT_OPTIONS[15].family; // Bebas Neue

async function getAudioDuration(url: string): Promise<number> {
  return new Promise((res) => {
    const a = new Audio();
    a.preload = "metadata";
    a.src = url;
    a.onloadedmetadata = () => res(Number.isFinite(a.duration) ? a.duration : 0);
    a.onerror = () => res(0);
  });
}

function nextZOrderName(prefix: string, existing: Layer[]): string {
  const count = existing.filter((l) => l.name.startsWith(prefix)).length;
  return `${prefix} ${count + 1}`;
}

export const useStudio = create<StudioState>((set, get) => ({
  activeMenu: "audio",
  setActiveMenu: (id) =>
    set((s) => ({ activeMenu: s.activeMenu === id ? null : id })),

  aspect: DEFAULT_ASPECT_RATIO,
  setAspect: (id) =>
    set({ aspect: ASPECT_RATIOS.find((a) => a.id === id) ?? DEFAULT_ASPECT_RATIO }),

  tracks: [],
  currentTrackId: null,
  beatSensitivity: 0.55,
  setBeatSensitivity: (v) => set({ beatSensitivity: v }),
  loopPlaylist: true,
  setLoopPlaylist: (v) => set({ loopPlaylist: v }),
  addTracks: async (files) => {
    const created: AudioTrack[] = [];
    for (const file of files) {
      const url = URL.createObjectURL(file);
      const duration = await getAudioDuration(url);
      created.push({
        id: nanoid(),
        name: file.name,
        file,
        url,
        duration,
      });
    }
    set((s) => {
      const tracks = [...s.tracks, ...created];
      const currentTrackId = s.currentTrackId ?? tracks[0]?.id ?? null;
      return { tracks, currentTrackId };
    });
  },
  removeTrack: (id) =>
    set((s) => {
      const tracks = s.tracks.filter((t) => t.id !== id);
      const target = s.tracks.find((t) => t.id === id);
      if (target) URL.revokeObjectURL(target.url);
      const currentTrackId =
        s.currentTrackId === id ? (tracks[0]?.id ?? null) : s.currentTrackId;
      return { tracks, currentTrackId };
    }),
  setCurrentTrack: (id) => set({ currentTrackId: id }),
  reorderTracks: (from, to) =>
    set((s) => {
      const tracks = [...s.tracks];
      const [item] = tracks.splice(from, 1);
      tracks.splice(to, 0, item);
      return { tracks };
    }),

  layers: [],
  selectedLayerId: null,
  setSelectedLayer: (id) => set({ selectedLayerId: id }),

  addImageLayer: async (file) => {
    const src = URL.createObjectURL(file);
    const layer: ImageLayer = {
      id: nanoid(),
      type: "image",
      name: nextZOrderName("Image", get().layers),
      visible: true,
      locked: false,
      x: 0.35,
      y: 0.35,
      width: 0.3,
      height: 0.3,
      rotation: 0,
      opacity: 1,
      src,
      fileName: file.name,
      shape: "original",
      rotateMode: "none",
      rotateSpeed: 30,
      transparency: 1,
      beatZoom: false,
      beatZoomAmount: 0.18,
      beatDivision: 1,
      outlineWidth: 0,
      outlineColor: "#ffffff",
    };
    set((s) => ({
      layers: [...s.layers, layer],
      selectedLayerId: layer.id,
    }));
  },

  addTextLayer: () => {
    const layer: TextLayer = {
      id: nanoid(),
      type: "text",
      name: nextZOrderName("Text", get().layers),
      visible: true,
      locked: false,
      x: 0.1,
      y: 0.08,
      width: 0.8,
      height: 0.12,
      rotation: 0,
      opacity: 1,
      text: "Your Text Here",
      fontFamily: DEFAULT_FONT,
      fontSize: 84,
      fontWeight: 700,
      italic: false,
      color: "#ffffff",
      strokeColor: "#000000",
      strokeWidth: 0,
      shadow: true,
      shadowColor: "#000000",
      letterSpacing: 0,
      align: "center",
      beatZoom: false,
      beatZoomAmount: 0.12,
    };
    set((s) => ({ layers: [...s.layers, layer], selectedLayerId: layer.id }));
  },

  addVisualizerLayer: (presetId) => {
    const preset = VISUALIZER_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    const layer: VisualizerLayer = {
      id: nanoid(),
      type: "visualizer",
      name: `${preset.name}`,
      visible: true,
      locked: false,
      x: 0.05,
      y: 0.55,
      width: 0.9,
      height: 0.35,
      rotation: 0,
      opacity: 1,
      presetId,
      colorA: preset.colorA,
      colorB: preset.colorB,
      glow: preset.glow,
      smoothing: preset.smoothing,
      bars: preset.bars,
      thickness: preset.thickness,
      mirror: false,
    };
    set((s) => ({ layers: [...s.layers, layer], selectedLayerId: layer.id }));
  },

  addBackgroundLayer: () => {
    const existing = get().layers.find((l) => l.type === "background");
    if (existing) {
      set({ selectedLayerId: existing.id });
      return;
    }
    const layer: BackgroundLayer = {
      id: nanoid(),
      type: "background",
      name: "Background",
      visible: true,
      locked: true,
      x: 0,
      y: 0,
      width: 1,
      height: 1,
      rotation: 0,
      opacity: 1,
      items: [],
      intervalSec: 6,
      crossfadeSec: 1.4,
      blur: 0,
      brightness: 1,
      fit: "cover" as BackgroundFit,
    };
    set((s) => ({
      layers: [layer, ...s.layers], // backgrounds at bottom of z-stack (rendered first)
      selectedLayerId: layer.id,
    }));
  },

  addBackgroundItems: (layerId, files) =>
    set((s) => {
      const layers = s.layers.map((l) => {
        if (l.id !== layerId || l.type !== "background") return l;
        const items: BackgroundItem[] = [
          ...l.items,
          ...files.map<BackgroundItem>((f) => ({
            id: nanoid(),
            kind: f.type.startsWith("video/") ? "video" : "image",
            src: URL.createObjectURL(f),
            fileName: f.name,
          })),
        ];
        return { ...l, items } satisfies BackgroundLayer;
      });
      return { layers };
    }),

  removeBackgroundItem: (layerId, itemId) =>
    set((s) => ({
      layers: s.layers.map((l) => {
        if (l.id !== layerId || l.type !== "background") return l;
        const target = l.items.find((i) => i.id === itemId);
        if (target) URL.revokeObjectURL(target.src);
        return { ...l, items: l.items.filter((i) => i.id !== itemId) };
      }),
    })),

  addEffectLayer: (presetId) => {
    const preset = EFFECT_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    const layer: EffectLayer = {
      id: nanoid(),
      type: "effect",
      name: preset.name,
      visible: true,
      locked: false,
      x: 0,
      y: 0,
      width: 1,
      height: 1,
      rotation: 0,
      opacity: 1,
      presetId,
      intensity: 0.6,
      speed: 1,
      beatReactive: true,
    };
    set((s) => ({ layers: [...s.layers, layer], selectedLayerId: layer.id }));
  },

  addLyricsLayer: () => {
    const layer: LyricsLayer = {
      id: nanoid(),
      type: "lyrics",
      name: nextZOrderName("Lyrics", get().layers),
      visible: true,
      locked: false,
      x: 0.1,
      y: 0.78,
      width: 0.8,
      height: 0.14,
      rotation: 0,
      opacity: 1,
      lines: [],
      fontFamily: DEFAULT_FONT,
      fontSize: 80,
      fontWeight: 700,
      italic: false,
      color: "#ffffff",
      highlightColor: "#21d4fd",
      strokeColor: "#000000",
      strokeWidth: 0,
      shadow: true,
      align: "center",
      animation: "fade",
      style: "plain",
      beatZoom: false,
      beatZoomAmount: 0.1,
    };
    set((s) => ({ layers: [...s.layers, layer], selectedLayerId: layer.id }));
  },

  removeLayer: (id) =>
    set((s) => {
      const removed = s.layers.find((l) => l.id === id);
      if (removed?.type === "image" && removed.src) {
        URL.revokeObjectURL(removed.src);
      }
      if (removed?.type === "background") {
        for (const item of removed.items) URL.revokeObjectURL(item.src);
      }
      return {
        layers: s.layers.filter((l) => l.id !== id),
        selectedLayerId:
          s.selectedLayerId === id ? null : s.selectedLayerId,
      };
    }),

  toggleLayerVisible: (id) =>
    set((s) => ({
      layers: s.layers.map((l) =>
        l.id === id ? { ...l, visible: !l.visible } : l,
      ),
    })),

  toggleLayerLocked: (id) =>
    set((s) => ({
      layers: s.layers.map((l) =>
        l.id === id ? { ...l, locked: !l.locked } : l,
      ),
    })),

  moveLayer: (id, dir) =>
    set((s) => {
      const idx = s.layers.findIndex((l) => l.id === id);
      if (idx < 0) return {};
      const target = idx + dir;
      if (target < 0 || target >= s.layers.length) return {};
      const layers = [...s.layers];
      [layers[idx], layers[target]] = [layers[target], layers[idx]];
      return { layers };
    }),

  updateLayer: (id, patch) =>
    set((s) => ({
      layers: s.layers.map((l) =>
        l.id === id ? ({ ...l, ...patch } as Layer) : l,
      ),
    })),

  groqKeys: [],
  addGroqKey: (name, key) =>
    set((s) => ({
      groqKeys: [...s.groqKeys, { id: nanoid(), name, key }],
    })),
  removeGroqKey: (id) =>
    set((s) => ({ groqKeys: s.groqKeys.filter((k) => k.id !== id) })),
  setLyrics: (layerId, lines) =>
    set((s) => ({
      layers: s.layers.map((l) =>
        l.id === layerId && l.type === "lyrics" ? { ...l, lines } : l,
      ),
    })),

  exportSettings: {
    width: DEFAULT_ASPECT_RATIO.w,
    height: DEFAULT_ASPECT_RATIO.h,
    fps: 30,
    bitrateMbps: 8,
    format: "webm",
  },
  setExport: (patch) =>
    set((s) => ({ exportSettings: { ...s.exportSettings, ...patch } })),

  playing: false,
  setPlaying: (v) => set({ playing: v }),
  currentTime: 0,
  duration: 0,
  setPlaybackTime: (t, d) => set({ currentTime: t, duration: d }),
  detectedBpm: 0,
  setDetectedBpm: (v) => set({ detectedBpm: v }),
}));
