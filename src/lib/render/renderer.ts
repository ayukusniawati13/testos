import type { Layer, VisualizerLayer, EffectLayer } from "@/types/studio";
import { AudioEngine } from "@/lib/audio/engine";
import { drawVisualizer } from "./visualizers";
import { drawEffect } from "./effects";
import {
  drawBackground,
  drawImageLayer,
  drawLyricsLayer,
  drawTextLayer,
} from "./draw";

export interface SceneAccessor {
  layers: () => Layer[];
  canvasW: () => number;
  canvasH: () => number;
}

/**
 * Renders one frame of the studio scene to the provided canvas.
 * Returns the audio engine snapshot for syncing UI state.
 */
export function renderFrame(
  canvas: HTMLCanvasElement,
  scene: SceneAccessor,
  elapsedMs: number,
  dtMs: number,
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  const W = scene.canvasW();
  const H = scene.canvasH();
  if (canvas.width !== W) canvas.width = W;
  if (canvas.height !== H) canvas.height = H;

  // background fill
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, W, H);

  const engine = AudioEngine.get();
  const snap = engine.tick();
  const baseDraw = {
    ctx,
    canvasW: W,
    canvasH: H,
    elapsedMs,
    beatPulse: snap.beat.pulse,
  } as const;
  const fxCtx = {
    ctx,
    width: W,
    height: H,
    elapsedMs,
    dtMs,
    beatPulse: snap.beat.pulse,
    beatHit: snap.beat.pulse > 0.95,
    bass: snap.beat.bass,
    mid: snap.beat.mid,
  } as const;

  const layers = scene.layers();
  for (const l of layers) {
    if (!l.visible) continue;
    switch (l.type) {
      case "background":
        drawBackground(l, baseDraw);
        break;
      case "image":
        drawImageLayer(l, baseDraw);
        break;
      case "text":
        drawTextLayer(l, baseDraw);
        break;
      case "lyrics":
        drawLyricsLayer(l, baseDraw, snap.currentTime);
        break;
      case "visualizer":
        renderVisualizerLayer(l, baseDraw, snap);
        break;
      case "effect":
        renderEffectLayer(l, fxCtx);
        break;
    }
  }
  return snap;
}

function renderVisualizerLayer(
  layer: VisualizerLayer,
  base: { ctx: CanvasRenderingContext2D; canvasW: number; canvasH: number; elapsedMs: number; beatPulse: number },
  snap: ReturnType<AudioEngine["tick"]>,
) {
  const { ctx, canvasW: W, canvasH: H } = base;
  const x = layer.x * W;
  const y = layer.y * H;
  const w = layer.width * W;
  const h = layer.height * H;
  ctx.save();
  ctx.translate(x, y);
  ctx.beginPath();
  ctx.rect(0, 0, w, h);
  ctx.clip();
  drawVisualizer(layer, {
    ctx,
    freq: snap.freq,
    time: snap.time,
    beatPulse: snap.beat.pulse,
    elapsedMs: base.elapsedMs,
    width: w,
    height: h,
  });
  ctx.restore();
}

function renderEffectLayer(
  layer: EffectLayer,
  fxCtx: {
    ctx: CanvasRenderingContext2D;
    width: number;
    height: number;
    elapsedMs: number;
    dtMs: number;
    beatPulse: number;
    beatHit: boolean;
    bass: number;
    mid: number;
  },
) {
  drawEffect(layer, fxCtx);
}
