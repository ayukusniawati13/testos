import type {
  BackgroundLayer,
  ImageLayer,
  LyricsLayer,
  TextLayer,
} from "@/types/studio";
import { getFontStack } from "@/data/fonts";
import { getImage, getVideo } from "./assets";

export interface BaseDrawCtx {
  ctx: CanvasRenderingContext2D;
  canvasW: number;
  canvasH: number;
  elapsedMs: number;
  beatPulse: number;
}

// ============== BACKGROUND ==============
export function drawBackground(layer: BackgroundLayer, c: BaseDrawCtx) {
  const { ctx, canvasW: W, canvasH: H, elapsedMs } = c;
  if (layer.items.length === 0) return;

  // determine active item index based on intervalSec
  const slot = layer.intervalSec * 1000;
  const idx = Math.floor(elapsedMs / slot) % layer.items.length;
  const nextIdx = (idx + 1) % layer.items.length;
  const t = (elapsedMs % slot) / slot;
  const crossfade = layer.crossfadeSec * 1000 / slot; // fraction
  const fade = t > 1 - crossfade ? (t - (1 - crossfade)) / crossfade : 0;

  ctx.save();
  ctx.globalAlpha *= layer.opacity;
  if (layer.blur > 0) ctx.filter = `blur(${layer.blur}px) brightness(${layer.brightness})`;
  else if (layer.brightness !== 1) ctx.filter = `brightness(${layer.brightness})`;

  drawBgItem(ctx, layer, layer.items[idx], W, H, 1 - fade);
  if (layer.items.length > 1 && fade > 0) {
    drawBgItem(ctx, layer, layer.items[nextIdx], W, H, fade);
  }
  ctx.restore();
}

function drawBgItem(
  ctx: CanvasRenderingContext2D,
  layer: BackgroundLayer,
  item: BackgroundLayer["items"][number],
  W: number,
  H: number,
  alpha: number,
) {
  const el = item.kind === "video" ? getVideo(item.src) : getImage(item.src);
  if (!el) {
    ctx.globalAlpha *= alpha;
    ctx.fillStyle = "#0d0f17";
    ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha /= alpha;
    return;
  }
  const iw = "videoWidth" in el ? el.videoWidth : el.naturalWidth;
  const ih = "videoHeight" in el ? el.videoHeight : el.naturalHeight;
  if (!iw || !ih) return;
  const prev = ctx.globalAlpha;
  ctx.globalAlpha *= alpha;
  let dw: number, dh: number, dx: number, dy: number;
  if (layer.fit === "fill") {
    dx = 0;
    dy = 0;
    dw = W;
    dh = H;
  } else {
    const targetRatio = W / H;
    const ratio = iw / ih;
    const cover = layer.fit === "cover";
    if ((ratio > targetRatio) === cover) {
      dh = H;
      dw = ratio * dh;
      dx = (W - dw) / 2;
      dy = 0;
    } else {
      dw = W;
      dh = dw / ratio;
      dx = 0;
      dy = (H - dh) / 2;
    }
  }
  ctx.drawImage(el, dx, dy, dw, dh);
  ctx.globalAlpha = prev;
}

// ============== IMAGE ==============
export function drawImageLayer(layer: ImageLayer, c: BaseDrawCtx) {
  const { ctx, canvasW: W, canvasH: H, elapsedMs, beatPulse } = c;
  const img = getImage(layer.src);
  if (!img) return;

  const x = layer.x * W;
  const y = layer.y * H;
  const w = layer.width * W;
  const h = layer.height * H;
  const cx = x + w / 2;
  const cy = y + h / 2;

  // beat zoom amount (subdivide pulses for division>1)
  let zoom = 1;
  if (layer.beatZoom) {
    const div = layer.beatDivision;
    // For div=1 -> use beatPulse directly. For higher division use a faster decay envelope synced to elapsedMs.
    const env =
      div === 1
        ? beatPulse
        : Math.max(0, Math.sin((elapsedMs / 1000) * Math.PI * div * 2));
    zoom = 1 + env * layer.beatZoomAmount;
  }

  // rotation: layer.rotation (static) + rotateMode (continuous)
  let rotation = (layer.rotation * Math.PI) / 180;
  if (layer.rotateMode !== "none") {
    const speedRadPerSec = (layer.rotateSpeed * Math.PI) / 180;
    const sign = layer.rotateMode === "cw" ? 1 : -1;
    rotation += sign * speedRadPerSec * (elapsedMs / 1000);
  }

  ctx.save();
  ctx.globalAlpha *= layer.opacity * layer.transparency;
  ctx.translate(cx, cy);
  ctx.rotate(rotation);
  ctx.scale(zoom, zoom);

  if (layer.shape === "circle") {
    const r = Math.min(w, h) / 2;
    ctx.save();
    ctx.beginPath();
    ctx.arc(0, 0, r, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();
    ctx.drawImage(img, -r, -r, r * 2, r * 2);
    ctx.restore();
    if (layer.outlineWidth > 0) {
      ctx.strokeStyle = layer.outlineColor;
      ctx.lineWidth = layer.outlineWidth;
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();
    }
  } else if (layer.shape === "rounded") {
    const r = Math.min(w, h) * 0.12;
    ctx.save();
    roundRect(ctx, -w / 2, -h / 2, w, h, r);
    ctx.clip();
    ctx.drawImage(img, -w / 2, -h / 2, w, h);
    ctx.restore();
    if (layer.outlineWidth > 0) {
      ctx.strokeStyle = layer.outlineColor;
      ctx.lineWidth = layer.outlineWidth;
      roundRect(ctx, -w / 2, -h / 2, w, h, r);
      ctx.stroke();
    }
  } else {
    ctx.drawImage(img, -w / 2, -h / 2, w, h);
    if (layer.outlineWidth > 0) {
      ctx.strokeStyle = layer.outlineColor;
      ctx.lineWidth = layer.outlineWidth;
      ctx.strokeRect(-w / 2, -h / 2, w, h);
    }
  }
  ctx.restore();
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

// ============== TEXT ==============
export function drawTextLayer(layer: TextLayer, c: BaseDrawCtx) {
  const { ctx, canvasW: W, canvasH: H, beatPulse } = c;
  const x = layer.x * W;
  const y = layer.y * H;
  const w = layer.width * W;
  const h = layer.height * H;
  const cx = x + w / 2;
  const cy = y + h / 2;

  const zoom = layer.beatZoom ? 1 + beatPulse * layer.beatZoomAmount : 1;

  ctx.save();
  ctx.globalAlpha *= layer.opacity;
  ctx.translate(cx, cy);
  ctx.rotate((layer.rotation * Math.PI) / 180);
  ctx.scale(zoom, zoom);
  // Scale font size relative to canvas height (so 1080p reference looks same on any size)
  const fs = layer.fontSize * (H / 1080);
  const weight = layer.fontWeight;
  ctx.font = `${layer.italic ? "italic " : ""}${weight} ${fs}px ${getFontStack(layer.fontFamily)}`;
  ctx.textAlign = layer.align as CanvasTextAlign;
  ctx.textBaseline = "middle";

  if (layer.shadow) {
    ctx.shadowColor = layer.shadowColor;
    ctx.shadowBlur = fs * 0.18;
    ctx.shadowOffsetY = fs * 0.04;
  }

  const drawX = layer.align === "left" ? -w / 2 : layer.align === "right" ? w / 2 : 0;
  if (layer.strokeWidth > 0) {
    ctx.lineWidth = layer.strokeWidth * (H / 1080);
    ctx.strokeStyle = layer.strokeColor;
    ctx.strokeText(layer.text, drawX, 0);
  }
  ctx.fillStyle = layer.color;
  ctx.fillText(layer.text, drawX, 0);
  ctx.restore();
}

// ============== LYRICS ==============
export function drawLyricsLayer(
  layer: LyricsLayer,
  c: BaseDrawCtx,
  audioTime: number,
) {
  const { ctx, canvasW: W, canvasH: H, beatPulse } = c;
  if (layer.lines.length === 0) return;

  // Find current line + progress (for typewriter/karaoke)
  let line = layer.lines[0];
  for (const l of layer.lines) {
    if (audioTime >= l.time) line = l;
    else break;
  }
  if (audioTime < line.time || audioTime > line.time + line.duration + 0.6) return;
  const progress = Math.min(
    1,
    Math.max(0, (audioTime - line.time) / Math.max(0.1, line.duration)),
  );

  const x = layer.x * W;
  const y = layer.y * H;
  const w = layer.width * W;
  const h = layer.height * H;
  const cx = x + w / 2;
  const cy = y + h / 2;

  // animation: derive scale / alpha
  let scale = 1;
  let alpha = 1;
  let typeChars = line.text.length;
  let karaokeAdvance = 0;

  switch (layer.animation) {
    case "fade": {
      const fadeIn = Math.min(1, progress / 0.15);
      const fadeOut = Math.min(1, (1 - progress) / 0.15);
      alpha = Math.min(fadeIn, fadeOut);
      break;
    }
    case "typewriter":
      typeChars = Math.floor(progress * line.text.length);
      break;
    case "slide-up":
      alpha = Math.min(1, progress * 5);
      break;
    case "scale-pop":
      scale = 0.6 + Math.min(1, progress * 4) * 0.5;
      break;
    case "neon-glow":
      break;
    case "bounce":
      scale = 1 + Math.sin(progress * Math.PI * 6) * 0.05 * (1 - progress);
      break;
    case "karaoke":
      karaokeAdvance = progress;
      break;
  }

  const beatScale = layer.beatZoom ? 1 + beatPulse * layer.beatZoomAmount : 1;
  scale *= beatScale;

  ctx.save();
  ctx.globalAlpha *= layer.opacity * alpha;
  ctx.translate(cx, cy + (layer.animation === "slide-up" ? (1 - progress) * 20 : 0));
  ctx.scale(scale, scale);

  const fs = layer.fontSize * (H / 1080);
  ctx.font = `${layer.italic ? "italic " : ""}${layer.fontWeight} ${fs}px ${getFontStack(layer.fontFamily)}`;
  ctx.textAlign = layer.align as CanvasTextAlign;
  ctx.textBaseline = "middle";
  if (layer.shadow) {
    ctx.shadowColor = "#000";
    ctx.shadowBlur = fs * 0.18;
  }

  const text =
    layer.animation === "typewriter" ? line.text.slice(0, typeChars) : line.text;
  const drawX = layer.align === "left" ? -w / 2 : layer.align === "right" ? w / 2 : 0;

  if (layer.style === "neon" || layer.animation === "neon-glow") {
    ctx.shadowColor = layer.highlightColor;
    ctx.shadowBlur = fs * 0.5;
    ctx.fillStyle = layer.color;
    ctx.fillText(text, drawX, 0);
    ctx.shadowBlur = fs * 0.18;
  } else if (layer.style === "outline") {
    ctx.lineWidth = fs * 0.06;
    ctx.strokeStyle = layer.highlightColor;
    ctx.strokeText(text, drawX, 0);
    ctx.fillStyle = layer.color;
    ctx.fillText(text, drawX, 0);
  } else if (layer.style === "gradient") {
    const g = ctx.createLinearGradient(-w / 2, -fs / 2, w / 2, fs / 2);
    g.addColorStop(0, layer.color);
    g.addColorStop(1, layer.highlightColor);
    ctx.fillStyle = g;
    ctx.fillText(text, drawX, 0);
  } else if (layer.style === "chrome") {
    const g = ctx.createLinearGradient(0, -fs / 2, 0, fs / 2);
    g.addColorStop(0, "#ffffff");
    g.addColorStop(0.5, layer.color);
    g.addColorStop(1, "#888888");
    ctx.fillStyle = g;
    ctx.fillText(text, drawX, 0);
  } else {
    if (layer.strokeWidth > 0) {
      ctx.lineWidth = layer.strokeWidth * (H / 1080);
      ctx.strokeStyle = layer.strokeColor;
      ctx.strokeText(text, drawX, 0);
    }
    ctx.fillStyle = layer.color;
    ctx.fillText(text, drawX, 0);
  }

  // Karaoke overlay
  if (layer.animation === "karaoke" && karaokeAdvance > 0) {
    const totalWidth = ctx.measureText(line.text).width;
    let leftEdge: number;
    if (layer.align === "left") leftEdge = drawX;
    else if (layer.align === "right") leftEdge = drawX - totalWidth;
    else leftEdge = -totalWidth / 2;
    const filledWidth = totalWidth * karaokeAdvance;
    ctx.save();
    ctx.beginPath();
    ctx.rect(leftEdge, -fs, filledWidth, fs * 2);
    ctx.clip();
    ctx.fillStyle = layer.highlightColor;
    ctx.fillText(line.text, drawX, 0);
    ctx.restore();
  }
  ctx.restore();
}
