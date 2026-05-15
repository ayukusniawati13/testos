/**
 * Caches HTMLImageElement / HTMLVideoElement instances keyed by URL.
 * Loads lazily so the renderer never blocks; first frame may show empty until
 * the image has decoded.
 */

interface ImageEntry {
  img: HTMLImageElement;
  ready: boolean;
}
interface VideoEntry {
  video: HTMLVideoElement;
  ready: boolean;
}

const images = new Map<string, ImageEntry>();
const videos = new Map<string, VideoEntry>();

export function getImage(src: string): HTMLImageElement | null {
  let e = images.get(src);
  if (!e) {
    const img = new Image();
    img.crossOrigin = "anonymous";
    e = { img, ready: false };
    images.set(src, e);
    img.onload = () => {
      e!.ready = true;
    };
    img.onerror = () => {
      images.delete(src);
    };
    img.src = src;
  }
  return e.ready ? e.img : null;
}

export function getVideo(src: string): HTMLVideoElement | null {
  let e = videos.get(src);
  if (!e) {
    const video = document.createElement("video");
    video.src = src;
    video.loop = true;
    video.muted = true;
    video.autoplay = true;
    video.playsInline = true;
    video.crossOrigin = "anonymous";
    e = { video, ready: false };
    videos.set(src, e);
    video.onloadeddata = () => {
      e!.ready = true;
      void video.play().catch(() => undefined);
    };
    video.onerror = () => {
      videos.delete(src);
    };
  }
  return e.ready ? e.video : null;
}

export function releaseSrc(src: string) {
  const i = images.get(src);
  if (i) {
    i.img.src = "";
    images.delete(src);
  }
  const v = videos.get(src);
  if (v) {
    v.video.pause();
    v.video.src = "";
    v.video.load();
    videos.delete(src);
  }
}
