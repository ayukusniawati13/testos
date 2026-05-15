import type {
  VisualizerLayer,
  VisualizerStyleId,
} from "@/types/studio";
import { VISUALIZER_PRESETS } from "@/data/visualizers";

export interface VizDrawCtx {
  ctx: CanvasRenderingContext2D;
  freq: Uint8Array;
  time: Uint8Array;
  beatPulse: number;
  /** ms since renderer start */
  elapsedMs: number;
  width: number;
  height: number;
}

function resolvePreset(layer: VisualizerLayer) {
  const preset = VISUALIZER_PRESETS.find((p) => p.id === layer.presetId);
  return {
    style: preset?.style ?? "bars",
    colorA: layer.colorA ?? preset?.colorA ?? "#7c5cff",
    colorB: layer.colorB ?? preset?.colorB ?? "#21d4fd",
    glow: layer.glow ?? preset?.glow ?? 0.7,
    smoothing: layer.smoothing ?? preset?.smoothing ?? 0.78,
    bars: layer.bars ?? preset?.bars ?? 64,
    thickness: layer.thickness ?? preset?.thickness ?? 4,
    mirror: layer.mirror ?? false,
  };
}

/**
 * Downsample frequency data (using log scale so we get more low-freq detail)
 * into `bars` bins, each in 0..1.
 */
function downsampleFreq(freq: Uint8Array, bars: number): number[] {
  const out: number[] = [];
  const usable = Math.floor(freq.length * 0.7); // skip very high freqs
  for (let i = 0; i < bars; i++) {
    const t0 = i / bars;
    const t1 = (i + 1) / bars;
    const start = Math.floor(Math.pow(t0, 1.7) * usable);
    const end = Math.max(start + 1, Math.floor(Math.pow(t1, 1.7) * usable));
    let sum = 0;
    let n = 0;
    for (let j = start; j < end && j < usable; j++) {
      sum += freq[j];
      n++;
    }
    out.push((sum / Math.max(1, n)) / 255);
  }
  return out;
}

function gradient(
  ctx: CanvasRenderingContext2D,
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  a: string,
  b: string,
) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  g.addColorStop(0, a);
  g.addColorStop(1, b);
  return g;
}

function setGlow(ctx: CanvasRenderingContext2D, color: string, amount: number) {
  ctx.shadowColor = color;
  ctx.shadowBlur = 8 + amount * 32;
}

export function drawVisualizer(layer: VisualizerLayer, c: VizDrawCtx) {
  const opts = resolvePreset(layer);
  const { ctx, width: W, height: H } = c;
  ctx.save();
  ctx.globalAlpha = layer.opacity;
  setGlow(ctx, opts.colorA, opts.glow);

  switch (opts.style as VisualizerStyleId) {
    case "bars":
      drawBars(c, opts, false);
      break;
    case "bars-mirror":
      drawBars(c, opts, true);
      break;
    case "circle-bars":
      drawCircleBars(c, opts);
      break;
    case "circle-wave":
      drawCircleWave(c, opts);
      break;
    case "wave":
      drawWave(c, opts, false);
      break;
    case "wave-area":
      drawWave(c, opts, true);
      break;
    case "rings":
      drawRings(c, opts);
      break;
    case "dots":
      drawDots(c, opts);
      break;
    case "ribbon":
      drawRibbon(c, opts);
      break;
    case "particles":
      drawParticles(c, opts);
      break;
    case "spiral":
      drawSpiral(c, opts);
      break;
    case "polygon":
      drawPolygon(c, opts);
      break;
    case "stairs":
      drawStairs(c, opts);
      break;
    case "blocks":
      drawBlocks(c, opts);
      break;
    default:
      drawBars(c, opts, false);
  }

  ctx.restore();
  // shadowBlur outside save state is wasteful but resetting explicitly:
  void H;
  void W;
}

type Opts = ReturnType<typeof resolvePreset>;

function drawBars(c: VizDrawCtx, opts: Opts, mirror: boolean) {
  const { ctx, freq, width: W, height: H } = c;
  const bars = downsampleFreq(freq, opts.bars);
  const gap = W / opts.bars / 6;
  const bw = W / opts.bars - gap;
  const baseY = mirror ? H * 0.55 : H;
  for (let i = 0; i < opts.bars; i++) {
    const v = bars[i];
    const h = v * H * (mirror ? 0.45 : 0.95);
    const x = i * (bw + gap) + gap / 2;
    ctx.fillStyle = gradient(ctx, x, baseY - h, x, baseY, opts.colorB, opts.colorA);
    if (mirror) {
      ctx.fillRect(x, baseY - h, bw, h);
      ctx.fillStyle = gradient(ctx, x, baseY, x, baseY + h, opts.colorA, opts.colorB);
      ctx.globalAlpha *= 0.7;
      ctx.fillRect(x, baseY, bw, h);
      ctx.globalAlpha /= 0.7;
    } else {
      ctx.fillRect(x, baseY - h, bw, h);
    }
  }
}

function drawCircleBars(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H } = c;
  const bars = downsampleFreq(freq, opts.bars);
  const cx = W / 2;
  const cy = H / 2;
  const r = Math.min(W, H) * 0.22;
  ctx.lineWidth = Math.max(2, (Math.PI * 2 * r) / opts.bars / 1.8);
  for (let i = 0; i < opts.bars; i++) {
    const a = (i / opts.bars) * Math.PI * 2 - Math.PI / 2;
    const v = bars[i];
    const len = v * Math.min(W, H) * 0.32 + 6;
    const x0 = cx + Math.cos(a) * r;
    const y0 = cy + Math.sin(a) * r;
    const x1 = cx + Math.cos(a) * (r + len);
    const y1 = cy + Math.sin(a) * (r + len);
    ctx.strokeStyle = gradient(ctx, x0, y0, x1, y1, opts.colorA, opts.colorB);
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
  }
}

function drawCircleWave(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H } = c;
  const bars = downsampleFreq(freq, 180);
  const cx = W / 2;
  const cy = H / 2;
  const r = Math.min(W, H) * 0.28;
  ctx.lineWidth = opts.thickness;
  ctx.strokeStyle = gradient(ctx, 0, 0, W, H, opts.colorA, opts.colorB);
  ctx.beginPath();
  for (let i = 0; i <= bars.length; i++) {
    const v = bars[i % bars.length];
    const a = (i / bars.length) * Math.PI * 2;
    const rr = r + v * r * 0.7;
    const x = cx + Math.cos(a) * rr;
    const y = cy + Math.sin(a) * rr;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.stroke();
}

function drawWave(c: VizDrawCtx, opts: Opts, area: boolean) {
  const { ctx, time, width: W, height: H } = c;
  ctx.lineWidth = opts.thickness;
  ctx.strokeStyle = gradient(ctx, 0, 0, W, 0, opts.colorA, opts.colorB);
  ctx.fillStyle = ctx.strokeStyle;
  const cy = H / 2;
  ctx.beginPath();
  for (let i = 0; i < time.length; i++) {
    const x = (i / (time.length - 1)) * W;
    const v = (time[i] - 128) / 128;
    const y = cy + v * H * 0.4;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  if (area) {
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.globalAlpha *= 0.45;
    ctx.fill();
    ctx.globalAlpha /= 0.45;
    ctx.beginPath();
    for (let i = 0; i < time.length; i++) {
      const x = (i / (time.length - 1)) * W;
      const v = (time[i] - 128) / 128;
      const y = cy + v * H * 0.4;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
  }
  ctx.stroke();
}

function drawRings(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H, beatPulse } = c;
  const bars = downsampleFreq(freq, 6);
  const cx = W / 2;
  const cy = H / 2;
  const base = Math.min(W, H) * 0.12;
  for (let i = 0; i < 6; i++) {
    ctx.lineWidth = opts.thickness + 1;
    const v = bars[i];
    const r = base + i * (Math.min(W, H) * 0.05) + v * 40 + beatPulse * 20;
    ctx.strokeStyle = gradient(ctx, cx - r, cy, cx + r, cy, opts.colorA, opts.colorB);
    ctx.globalAlpha *= 0.85 - i * 0.1;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.globalAlpha /= 0.85 - i * 0.1;
  }
}

function drawDots(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H } = c;
  const bars = downsampleFreq(freq, opts.bars);
  for (let i = 0; i < opts.bars; i++) {
    const v = bars[i];
    const x = (i / (opts.bars - 1)) * W;
    const y = H - v * H * 0.85 - 12;
    const r = 4 + v * 16;
    ctx.fillStyle = gradient(ctx, x, y - r, x, y + r, opts.colorA, opts.colorB);
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawRibbon(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H, elapsedMs } = c;
  const bars = downsampleFreq(freq, opts.bars);
  ctx.lineWidth = opts.thickness + 2;
  ctx.strokeStyle = gradient(ctx, 0, 0, W, 0, opts.colorA, opts.colorB);
  ctx.beginPath();
  const phase = elapsedMs / 500;
  for (let i = 0; i < opts.bars; i++) {
    const x = (i / (opts.bars - 1)) * W;
    const v = bars[i];
    const y = H / 2 + Math.sin(phase + i * 0.2) * 40 - v * H * 0.4;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

interface ParticleState {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  color: string;
}
const particleCache = new WeakMap<VizDrawCtx["ctx"], ParticleState[]>();
function drawParticles(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H, beatPulse } = c;
  const bars = downsampleFreq(freq, 16);
  const bass = (bars[0] + bars[1] + bars[2]) / 3;
  let parts = particleCache.get(ctx);
  if (!parts) {
    parts = [];
    particleCache.set(ctx, parts);
  }
  const spawn = Math.floor(bass * 6 + beatPulse * 18);
  for (let i = 0; i < spawn; i++) {
    parts.push({
      x: W / 2,
      y: H / 2,
      vx: (Math.random() - 0.5) * 12,
      vy: (Math.random() - 0.5) * 12,
      life: 1,
      color: i % 2 ? opts.colorA : opts.colorB,
    });
  }
  for (let i = parts.length - 1; i >= 0; i--) {
    const p = parts[i];
    p.x += p.vx;
    p.y += p.vy;
    p.vy += 0.18;
    p.life -= 0.018;
    if (p.life <= 0) {
      parts.splice(i, 1);
      continue;
    }
    ctx.globalAlpha = p.life * 0.9;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3 + p.life * 4, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawSpiral(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H, elapsedMs } = c;
  const bars = downsampleFreq(freq, 180);
  const cx = W / 2;
  const cy = H / 2;
  ctx.lineWidth = opts.thickness;
  ctx.strokeStyle = gradient(ctx, 0, 0, W, H, opts.colorA, opts.colorB);
  ctx.beginPath();
  const phase = elapsedMs / 1000;
  for (let i = 0; i < bars.length; i++) {
    const t = i / bars.length;
    const v = bars[i];
    const r = t * Math.min(W, H) * 0.4 + v * 25;
    const a = t * Math.PI * 8 + phase;
    const x = cx + Math.cos(a) * r;
    const y = cy + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function drawPolygon(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H, beatPulse, elapsedMs } = c;
  const sides = 6;
  const bars = downsampleFreq(freq, sides);
  const cx = W / 2;
  const cy = H / 2;
  const r = Math.min(W, H) * 0.25 + beatPulse * 30;
  ctx.lineWidth = opts.thickness + 2;
  ctx.strokeStyle = gradient(ctx, 0, 0, W, H, opts.colorA, opts.colorB);
  const rot = elapsedMs / 2000;
  ctx.beginPath();
  for (let i = 0; i <= sides; i++) {
    const a = rot + (i / sides) * Math.PI * 2;
    const v = bars[i % sides];
    const rr = r + v * 60;
    const x = cx + Math.cos(a) * rr;
    const y = cy + Math.sin(a) * rr;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.stroke();
}

function drawStairs(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H } = c;
  const bars = downsampleFreq(freq, opts.bars);
  ctx.fillStyle = gradient(ctx, 0, 0, 0, H, opts.colorB, opts.colorA);
  ctx.beginPath();
  ctx.moveTo(0, H);
  for (let i = 0; i < opts.bars; i++) {
    const x = (i / opts.bars) * W;
    const x2 = ((i + 1) / opts.bars) * W;
    const y = H - bars[i] * H * 0.9;
    ctx.lineTo(x, y);
    ctx.lineTo(x2, y);
  }
  ctx.lineTo(W, H);
  ctx.closePath();
  ctx.fill();
}

function drawBlocks(c: VizDrawCtx, opts: Opts) {
  const { ctx, freq, width: W, height: H } = c;
  const cols = opts.bars;
  const rows = 14;
  const bars = downsampleFreq(freq, cols);
  const cellW = W / cols;
  const cellH = H / rows;
  for (let i = 0; i < cols; i++) {
    const v = bars[i];
    const lit = Math.round(v * rows);
    for (let r = 0; r < lit; r++) {
      const y = H - (r + 1) * cellH;
      const t = r / rows;
      ctx.fillStyle = t < 0.6 ? opts.colorA : opts.colorB;
      ctx.globalAlpha = 0.85;
      ctx.fillRect(i * cellW + 1, y + 1, cellW - 2, cellH - 2);
    }
  }
  ctx.globalAlpha = 1;
}
