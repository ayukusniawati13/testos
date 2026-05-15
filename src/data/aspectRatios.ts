import type { AspectRatio } from "@/types/studio";

export const ASPECT_RATIOS: AspectRatio[] = [
  { id: "16:9", label: "16:9 Landscape (YouTube)", w: 1920, h: 1080 },
  { id: "9:16", label: "9:16 Vertical (Reels/Shorts/TikTok)", w: 1080, h: 1920 },
  { id: "1:1", label: "1:1 Square (Instagram)", w: 1080, h: 1080 },
  { id: "4:5", label: "4:5 Portrait (Instagram)", w: 1080, h: 1350 },
  { id: "4:3", label: "4:3 Classic", w: 1440, h: 1080 },
  { id: "3:4", label: "3:4 Portrait", w: 1080, h: 1440 },
  { id: "21:9", label: "21:9 Cinematic", w: 2560, h: 1080 },
];

export const DEFAULT_ASPECT_RATIO = ASPECT_RATIOS[0];
