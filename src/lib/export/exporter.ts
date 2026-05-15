import { AudioEngine } from "@/lib/audio/engine";

export interface ExportOptions {
  canvas: HTMLCanvasElement;
  fps: 24 | 30 | 60;
  bitrateMbps: number;
  format: "webm" | "mp4";
  filename?: string;
  /** If true, stops automatically when audio ends. */
  stopOnAudioEnd: boolean;
  onProgress?: (seconds: number) => void;
}

export interface ExportHandle {
  stop: () => void;
  promise: Promise<Blob>;
}

const PREFERRED_TYPES: { ext: string; mime: string }[] = [
  { ext: "webm", mime: "video/webm;codecs=vp9,opus" },
  { ext: "webm", mime: "video/webm;codecs=vp8,opus" },
  { ext: "webm", mime: "video/webm" },
  { ext: "mp4", mime: "video/mp4;codecs=avc1,mp4a" },
  { ext: "mp4", mime: "video/mp4" },
];

function pickType(format: "webm" | "mp4"): { ext: string; mime: string } | null {
  const candidates = PREFERRED_TYPES.filter((t) => t.ext === format);
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c.mime)) return c;
  }
  // fall back to anything supported
  for (const c of PREFERRED_TYPES) {
    if (MediaRecorder.isTypeSupported(c.mime)) return c;
  }
  return null;
}

export function startExport(opts: ExportOptions): ExportHandle {
  const stream = opts.canvas.captureStream(opts.fps);
  const audioStream = AudioEngine.get().getOutputStream();
  for (const t of audioStream.getAudioTracks()) stream.addTrack(t);

  const picked = pickType(opts.format);
  if (!picked) {
    return {
      stop: () => undefined,
      promise: Promise.reject(
        new Error("No supported video codec found in this browser"),
      ),
    };
  }
  const rec = new MediaRecorder(stream, {
    mimeType: picked.mime,
    videoBitsPerSecond: opts.bitrateMbps * 1_000_000,
  });
  const chunks: Blob[] = [];
  rec.ondataavailable = (e) => {
    if (e.data && e.data.size) chunks.push(e.data);
  };

  // Restart playback from 0 so the export captures everything
  const audio = AudioEngine.get().audio;
  audio.currentTime = 0;
  void AudioEngine.get().play();

  let progressInterval = 0;
  let stopped = false;
  let onEnded: (() => void) | null = null;

  const promise = new Promise<Blob>((resolve, reject) => {
    rec.onstop = () => {
      clearInterval(progressInterval);
      const type = picked.mime.split(";")[0];
      const blob = new Blob(chunks, { type });
      const filename =
        opts.filename ??
        `music-video-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}.${picked.ext}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 5000);
      resolve(blob);
    };
    rec.onerror = (e) =>
      reject(e instanceof Error ? e : new Error("MediaRecorder error"));
    rec.start(250);
    progressInterval = window.setInterval(() => {
      opts.onProgress?.(audio.currentTime);
    }, 200);
    if (opts.stopOnAudioEnd) {
      onEnded = () => {
        if (!stopped) rec.stop();
      };
      audio.addEventListener("ended", onEnded, { once: true });
    }
  }).finally(() => {
    if (onEnded) audio.removeEventListener("ended", onEnded);
  });

  return {
    stop: () => {
      stopped = true;
      if (rec.state !== "inactive") rec.stop();
    },
    promise,
  };
}
