import type { EffectKind, EffectLayer } from "@/types/studio";
import { EFFECT_PRESETS } from "@/data/effects";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  rot: number;
  vr: number;
  hue: number;
  life: number;
  maxLife: number;
}

interface EffectRuntime {
  particles: Particle[];
  lastSpawn: number;
  /** Used for some effects like neon-grid, lightning. */
  flash: number;
}

// Per-layer runtime keyed by layer id
const runtimes = new Map<string, EffectRuntime>();
function getRuntime(id: string): EffectRuntime {
  let r = runtimes.get(id);
  if (!r) {
    r = { particles: [], lastSpawn: 0, flash: 0 };
    runtimes.set(id, r);
  }
  return r;
}

export interface FxDrawCtx {
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  /** ms since renderer start */
  elapsedMs: number;
  /** ms since last frame (clamped) */
  dtMs: number;
  beatPulse: number;
  beatHit: boolean;
  bass: number;
  mid: number;
}

export function drawEffect(layer: EffectLayer, c: FxDrawCtx) {
  const preset = EFFECT_PRESETS.find((p) => p.id === layer.presetId);
  if (!preset) return;
  const runtime = getRuntime(layer.id);
  const { ctx } = c;
  ctx.save();
  ctx.globalAlpha *= layer.opacity;

  switch (preset.kind) {
    case "rain":
      stepRain(layer, c, runtime, 1);
      break;
    case "heavy-rain":
      stepRain(layer, c, runtime, 2.4);
      break;
    case "snow":
      stepSnow(layer, c, runtime, 1);
      break;
    case "blizzard":
      stepSnow(layer, c, runtime, 2.2);
      break;
    case "fog":
      stepFog(layer, c, runtime);
      break;
    case "lightning":
      stepLightning(layer, c, runtime);
      break;
    case "fireflies":
      stepFireflies(layer, c, runtime);
      break;
    case "bubbles":
      stepBubbles(layer, c, runtime);
      break;
    case "leaves":
      stepLeaves(layer, c, runtime, "🍂");
      break;
    case "petals":
      stepLeaves(layer, c, runtime, "🌸");
      break;
    case "dust":
      stepDust(layer, c, runtime);
      break;
    case "embers":
      stepEmbers(layer, c, runtime);
      break;
    case "smoke":
      stepSmoke(layer, c, runtime);
      break;
    case "sparkles":
      stepSparkles(layer, c, runtime);
      break;
    case "stars":
      stepStars(layer, c, runtime);
      break;
    case "shooting-stars":
      stepShootingStars(layer, c, runtime);
      break;
    case "hearts":
      stepEmoji(layer, c, runtime, "❤", "#ff4d6d");
      break;
    case "music-notes":
      stepEmoji(layer, c, runtime, "♪", layer.color ?? "#ffffff");
      break;
    case "confetti":
      stepConfetti(layer, c, runtime);
      break;
    case "fireworks":
      stepFireworks(layer, c, runtime);
      break;
    case "rays":
      stepRays(layer, c, runtime);
      break;
    case "neon-grid":
      stepNeonGrid(layer, c);
      break;
    case "glitch":
      stepGlitch(layer, c, runtime);
      break;
  }

  ctx.restore();
}

// =================== EFFECT IMPLEMENTATIONS ===================

function intensityToSpawnRate(layer: EffectLayer): number {
  return 0.5 + layer.intensity * 6;
}

function beatBoost(c: FxDrawCtx, layer: EffectLayer): number {
  return layer.beatReactive ? 1 + c.beatPulse * 2 : 1;
}

function stepRain(
  layer: EffectLayer,
  c: FxDrawCtx,
  r: EffectRuntime,
  factor: number,
) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * factor * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: -10,
      vx: -2,
      vy: 24 + Math.random() * 16,
      size: 1 + Math.random() * 1.5,
      rot: 0,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.strokeStyle = layer.color ?? "rgba(180, 210, 255, 0.65)";
  ctx.lineWidth = 1.4;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(p.x + p.vx * 0.6, p.y - p.vy * 0.6);
    ctx.stroke();
    if (p.y > H + 20) r.particles.splice(i, 1);
  }
}

function stepSnow(
  layer: EffectLayer,
  c: FxDrawCtx,
  r: EffectRuntime,
  factor: number,
) {
  const { ctx, width: W, height: H, dtMs, elapsedMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * factor * 0.6 * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: -10,
      vx: (Math.random() - 0.5) * 0.6,
      vy: 0.6 + Math.random() * 1.6,
      size: 1 + Math.random() * 3,
      rot: 0,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.fillStyle = layer.color ?? "rgba(255,255,255,0.9)";
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed + Math.sin((elapsedMs + i * 67) / 800) * 0.3;
    p.y += p.vy * layer.speed;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
    if (p.y > H + 10) r.particles.splice(i, 1);
  }
}

function stepFog(layer: EffectLayer, c: FxDrawCtx, _r: EffectRuntime) {
  const { ctx, width: W, height: H, elapsedMs } = c;
  void _r;
  ctx.globalAlpha *= 0.45 * layer.intensity * (0.6 + 0.4 * Math.sin(elapsedMs / 7000));
  ctx.fillStyle = layer.color ?? "rgba(200,210,230,1)";
  ctx.filter = "blur(60px)";
  for (let i = 0; i < 4; i++) {
    const t = (elapsedMs / 8000 + i * 0.25) % 1;
    const x = -W * 0.3 + t * W * 1.5;
    ctx.beginPath();
    ctx.ellipse(x, H * (0.4 + 0.1 * i), W * 0.45, H * 0.18, 0, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.filter = "none";
}

function stepLightning(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, beatHit, beatPulse } = c;
  if (beatHit && Math.random() < 0.3 + layer.intensity * 0.4) r.flash = 1;
  r.flash = Math.max(0, r.flash - 0.04);
  if (r.flash > 0.05) {
    ctx.fillStyle = `rgba(255,255,255,${r.flash * 0.4})`;
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = layer.color ?? "#cfe9ff";
    ctx.lineWidth = 3 + beatPulse * 4;
    ctx.beginPath();
    let x = W * 0.3 + Math.random() * W * 0.4;
    let y = 0;
    ctx.moveTo(x, y);
    while (y < H) {
      x += (Math.random() - 0.5) * 80;
      y += 30 + Math.random() * 60;
      ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

function stepFireflies(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs, elapsedMs } = c;
  const target = Math.floor(20 + layer.intensity * 80);
  while (r.particles.length < target) {
    r.particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      size: 1 + Math.random() * 3,
      rot: Math.random() * Math.PI * 2,
      vr: 0,
      hue: Math.random() * 60 + 40,
      life: Math.random(),
      maxLife: 1,
    });
  }
  ctx.shadowBlur = 14;
  for (const p of r.particles) {
    p.x += p.vx * layer.speed * (dtMs / 16);
    p.y += p.vy * layer.speed * (dtMs / 16);
    if (p.x < -10) p.x = W + 10;
    if (p.x > W + 10) p.x = -10;
    if (p.y < -10) p.y = H + 10;
    if (p.y > H + 10) p.y = -10;
    const blink = 0.4 + 0.6 * Math.sin(elapsedMs / 400 + p.rot);
    ctx.shadowColor = layer.color ?? `hsl(${p.hue},100%,60%)`;
    ctx.fillStyle = layer.color ?? `hsl(${p.hue},100%,70%)`;
    ctx.globalAlpha = blink * 0.85;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;
}

function stepBubbles(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * 0.5 * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: H + 20,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -(0.5 + Math.random() * 1.4),
      size: 4 + Math.random() * 16,
      rot: 0,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.lineWidth = 1.5;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    ctx.strokeStyle = layer.color ?? "rgba(200,230,255,0.8)";
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.stroke();
    if (p.y < -30) r.particles.splice(i, 1);
  }
}

function stepLeaves(
  layer: EffectLayer,
  c: FxDrawCtx,
  r: EffectRuntime,
  emoji: string,
) {
  const { ctx, width: W, height: H, dtMs, elapsedMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * 0.25 * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: -30,
      vx: (Math.random() - 0.5) * 1,
      vy: 1 + Math.random() * 1.4,
      size: 18 + Math.random() * 18,
      rot: Math.random() * Math.PI * 2,
      vr: (Math.random() - 0.5) * 0.04,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed + Math.sin((elapsedMs + i * 50) / 700) * 0.6;
    p.y += p.vy * layer.speed;
    p.rot += p.vr;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.font = `${p.size}px serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(emoji, 0, 0);
    ctx.restore();
    if (p.y > H + 40) r.particles.splice(i, 1);
  }
}

function stepDust(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs } = c;
  const target = Math.floor(40 + layer.intensity * 200);
  while (r.particles.length < target) {
    r.particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: 0.6 + Math.random() * 1.6,
      rot: 0,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.fillStyle = layer.color ?? "rgba(255,255,255,0.65)";
  for (const p of r.particles) {
    p.x += p.vx * layer.speed * (dtMs / 16);
    p.y += p.vy * layer.speed * (dtMs / 16);
    if (p.x < 0) p.x = W;
    if (p.x > W) p.x = 0;
    if (p.y < 0) p.y = H;
    if (p.y > H) p.y = 0;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  }
}

function stepEmbers(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * beatBoost(c, layer) * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: H + 10,
      vx: (Math.random() - 0.5) * 1,
      vy: -(1 + Math.random() * 3),
      size: 1 + Math.random() * 3,
      rot: 0,
      vr: 0,
      hue: 20 + Math.random() * 30,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.shadowBlur = 10;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    p.vy += 0.02;
    p.life -= 0.01;
    if (p.life <= 0 || p.y < -30) {
      r.particles.splice(i, 1);
      continue;
    }
    ctx.shadowColor = layer.color ?? `hsl(${p.hue},100%,55%)`;
    ctx.fillStyle = layer.color ?? `hsl(${p.hue},100%,60%)`;
    ctx.globalAlpha = p.life * 0.9;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;
}

function stepSmoke(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * 0.3 * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: W / 2 + (Math.random() - 0.5) * W * 0.6,
      y: H + 30,
      vx: (Math.random() - 0.5) * 0.3,
      vy: -(0.5 + Math.random() * 1.2),
      size: 40 + Math.random() * 80,
      rot: 0,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.filter = "blur(20px)";
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    p.life -= 0.004;
    if (p.life <= 0) {
      r.particles.splice(i, 1);
      continue;
    }
    ctx.globalAlpha = p.life * 0.35;
    ctx.fillStyle = layer.color ?? "rgba(180,180,200,1)";
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.filter = "none";
  ctx.globalAlpha = 1;
}

function stepSparkles(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * beatBoost(c, layer) * 0.6 * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: 0,
      vy: 0,
      size: 4 + Math.random() * 6,
      rot: Math.random() * Math.PI,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.shadowBlur = 14;
  ctx.shadowColor = layer.color ?? "#ffffff";
  ctx.strokeStyle = layer.color ?? "#ffffff";
  ctx.lineWidth = 1.4;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.life -= 0.04;
    if (p.life <= 0) {
      r.particles.splice(i, 1);
      continue;
    }
    ctx.globalAlpha = p.life;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.beginPath();
    ctx.moveTo(-p.size, 0);
    ctx.lineTo(p.size, 0);
    ctx.moveTo(0, -p.size);
    ctx.lineTo(0, p.size);
    ctx.stroke();
    ctx.restore();
  }
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;
}

function stepStars(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, elapsedMs } = c;
  const target = Math.floor(40 + layer.intensity * 220);
  while (r.particles.length < target) {
    r.particles.push({
      x: Math.random() * W,
      y: Math.random() * H,
      vx: 0,
      vy: 0,
      size: 0.5 + Math.random() * 2,
      rot: Math.random() * Math.PI * 2,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.fillStyle = layer.color ?? "#ffffff";
  for (const p of r.particles) {
    const tw = 0.5 + 0.5 * Math.sin(elapsedMs / 700 + p.rot);
    ctx.globalAlpha = tw;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function stepShootingStars(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H } = c;
  if (Math.random() < 0.02 * (0.4 + layer.intensity)) {
    r.particles.push({
      x: Math.random() * W,
      y: -10,
      vx: 12,
      vy: 5,
      size: 2,
      rot: 0,
      vr: 0,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.strokeStyle = layer.color ?? "#cfe9ff";
  ctx.lineWidth = 2;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    const tailX = p.x - p.vx * 8;
    const tailY = p.y - p.vy * 8;
    const grad = ctx.createLinearGradient(p.x, p.y, tailX, tailY);
    grad.addColorStop(0, layer.color ?? "#ffffff");
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.strokeStyle = grad;
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineTo(tailX, tailY);
    ctx.stroke();
    if (p.x > W + 30 || p.y > H + 30) r.particles.splice(i, 1);
  }
}

function stepEmoji(
  layer: EffectLayer,
  c: FxDrawCtx,
  r: EffectRuntime,
  emoji: string,
  color: string,
) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * 0.2 * (dtMs / 16));
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: H + 20,
      vx: (Math.random() - 0.5) * 0.6,
      vy: -(0.6 + Math.random() * 1.2),
      size: 20 + Math.random() * 20,
      rot: 0,
      vr: (Math.random() - 0.5) * 0.04,
      hue: 0,
      life: 1,
      maxLife: 1,
    });
  }
  ctx.fillStyle = color;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed + Math.sin(p.y / 60) * 0.5;
    p.y += p.vy * layer.speed;
    p.rot += p.vr;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.font = `${p.size}px serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(emoji, 0, 0);
    ctx.restore();
    if (p.y < -30) r.particles.splice(i, 1);
  }
}

function stepConfetti(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, dtMs } = c;
  const spawn = Math.floor(intensityToSpawnRate(layer) * beatBoost(c, layer) * 0.6 * (dtMs / 16));
  const colors = ["#ff5e5b", "#ffd166", "#06d6a0", "#118ab2", "#ff8fcf", "#a5ffd6"];
  for (let i = 0; i < spawn; i++) {
    r.particles.push({
      x: Math.random() * W,
      y: -10,
      vx: (Math.random() - 0.5) * 4,
      vy: 2 + Math.random() * 4,
      size: 6 + Math.random() * 8,
      rot: Math.random() * Math.PI * 2,
      vr: (Math.random() - 0.5) * 0.3,
      hue: i % colors.length,
      life: 1,
      maxLife: 1,
    });
  }
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i];
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    p.rot += p.vr;
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.rot);
    ctx.fillStyle = colors[p.hue];
    ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
    ctx.restore();
    if (p.y > H + 30) r.particles.splice(i, 1);
  }
}

function stepFireworks(layer: EffectLayer, c: FxDrawCtx, r: EffectRuntime) {
  const { ctx, width: W, height: H, beatHit } = c;
  if (beatHit && Math.random() < 0.6 * (0.4 + layer.intensity)) {
    const cx = Math.random() * W;
    const cy = Math.random() * H * 0.6;
    const color = `hsl(${Math.random() * 360},100%,60%)`;
    for (let i = 0; i < 60; i++) {
      const a = (i / 60) * Math.PI * 2;
      r.particles.push({
        x: cx,
        y: cy,
        vx: Math.cos(a) * (3 + Math.random() * 3),
        vy: Math.sin(a) * (3 + Math.random() * 3),
        size: 2,
        rot: 0,
        vr: 0,
        hue: 0,
        life: 1,
        maxLife: 1,
      });
      r.particles[r.particles.length - 1].rot = i;
      (r.particles[r.particles.length - 1] as Particle & { c?: string }).c = color;
    }
  }
  ctx.shadowBlur = 10;
  for (let i = r.particles.length - 1; i >= 0; i--) {
    const p = r.particles[i] as Particle & { c?: string };
    p.x += p.vx * layer.speed;
    p.y += p.vy * layer.speed;
    p.vy += 0.05;
    p.life -= 0.014;
    if (p.life <= 0) {
      r.particles.splice(i, 1);
      continue;
    }
    ctx.shadowColor = p.c ?? "#ffffff";
    ctx.fillStyle = p.c ?? "#ffffff";
    ctx.globalAlpha = p.life;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;
}

function stepRays(layer: EffectLayer, c: FxDrawCtx, _r: EffectRuntime) {
  void _r;
  const { ctx, width: W, height: H, elapsedMs } = c;
  ctx.translate(W / 2, -H * 0.1);
  ctx.rotate(Math.sin(elapsedMs / 6000) * 0.2);
  ctx.translate(-W / 2, H * 0.1);
  const rays = 14;
  for (let i = 0; i < rays; i++) {
    const a = (i / rays) * Math.PI * 2 + elapsedMs / 4000;
    const len = Math.max(W, H) * 1.2;
    ctx.save();
    ctx.translate(W / 2, H * 0.2);
    ctx.rotate(a);
    const grad = ctx.createLinearGradient(0, 0, 0, len);
    const col = layer.color ?? "#ffe1ad";
    grad.addColorStop(0, col);
    grad.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = grad;
    ctx.globalAlpha = 0.18 * layer.intensity;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(40, len);
    ctx.lineTo(-40, len);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }
}

function stepNeonGrid(layer: EffectLayer, c: FxDrawCtx) {
  const { ctx, width: W, height: H, elapsedMs } = c;
  const horizon = H * 0.55;
  ctx.strokeStyle = layer.color ?? "#21d4fd";
  ctx.shadowColor = ctx.strokeStyle;
  ctx.shadowBlur = 12;
  ctx.lineWidth = 1.5;
  ctx.globalAlpha = 0.85 * layer.intensity;
  // horizontal lines moving toward viewer
  for (let i = 0; i < 14; i++) {
    const t = (i / 14 + (elapsedMs / 2000) * layer.speed) % 1;
    const y = horizon + Math.pow(t, 2) * (H - horizon);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  // vertical lines converging at center
  for (let i = -8; i <= 8; i++) {
    const x = W / 2 + (i / 8) * W * 0.9;
    ctx.beginPath();
    ctx.moveTo(W / 2, horizon);
    ctx.lineTo(x, H);
    ctx.stroke();
  }
  ctx.shadowBlur = 0;
}

function stepGlitch(layer: EffectLayer, c: FxDrawCtx, _r: EffectRuntime) {
  void _r;
  const { ctx, width: W, height: H, beatPulse, elapsedMs } = c;
  ctx.globalAlpha = 0.4 + beatPulse * 0.4;
  for (let i = 0; i < 40 * layer.intensity; i++) {
    const y = Math.random() * H;
    const w = 20 + Math.random() * W * 0.4;
    const h = 1 + Math.random() * 6;
    const t = Math.sin(elapsedMs / 200 + i) * 0.5 + 0.5;
    ctx.fillStyle = t > 0.5 ? layer.color ?? "#21d4fd" : "#ff2bd6";
    ctx.fillRect(Math.random() * W, y, w, h);
  }
  ctx.globalAlpha = 1;
}

export function clearEffectRuntime(layerId: string) {
  runtimes.delete(layerId);
}

export function getEffectKind(presetId: string): EffectKind | undefined {
  return EFFECT_PRESETS.find((p) => p.id === presetId)?.kind;
}
