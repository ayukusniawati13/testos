import {
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { useStudio } from "@/store/studioStore";
import { renderFrame } from "@/lib/render/renderer";
import { AudioEngine } from "@/lib/audio/engine";
import type { Layer } from "@/types/studio";

type HandleId =
  | "move"
  | "n"
  | "s"
  | "e"
  | "w"
  | "ne"
  | "nw"
  | "se"
  | "sw";

interface DragState {
  layerId: string;
  handle: HandleId;
  startX: number; // pointer client x
  startY: number;
  startRect: { x: number; y: number; w: number; h: number };
  /** Pixel size of preview at drag start (snapshot) */
  previewW: number;
  previewH: number;
}

export function PreviewCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [previewSize, setPreviewSize] = useState({ w: 0, h: 0 });
  const aspect = useStudio((s) => s.aspect);
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const setSelectedLayer = useStudio((s) => s.setSelectedLayer);
  const updateLayer = useStudio((s) => s.updateLayer);
  const setPlaybackTime = useStudio((s) => s.setPlaybackTime);
  const setDetectedBpm = useStudio((s) => s.setDetectedBpm);
  const beatSensitivity = useStudio((s) => s.beatSensitivity);

  // Compute preview size to fit the parent while preserving aspect ratio
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const compute = () => {
      const rect = el.getBoundingClientRect();
      const target = aspect.w / aspect.h;
      let w = rect.width;
      let h = w / target;
      if (h > rect.height) {
        h = rect.height;
        w = h * target;
      }
      setPreviewSize({ w: Math.floor(w), h: Math.floor(h) });
    };
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, [aspect]);

  // Drive the render loop
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    let last = start;
    AudioEngine.get().setSensitivity(beatSensitivity);
    const loop = (now: number) => {
      const elapsed = now - start;
      const dt = Math.min(64, now - last);
      last = now;
      const canvas = canvasRef.current;
      if (canvas) {
        const snap = renderFrame(
          canvas,
          {
            layers: () => useStudio.getState().layers,
            canvasW: () => useStudio.getState().aspect.w,
            canvasH: () => useStudio.getState().aspect.h,
          },
          elapsed,
          dt,
        );
        if (snap) {
          setPlaybackTime(snap.currentTime, snap.duration);
          if (Math.abs(snap.beat.bpm - useStudio.getState().detectedBpm) > 0.5) {
            setDetectedBpm(snap.beat.bpm);
          }
        }
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update sensitivity when changed
  useEffect(() => {
    AudioEngine.get().setSensitivity(beatSensitivity);
  }, [beatSensitivity]);

  // ----- Drag / resize handling -----
  const dragRef = useRef<DragState | null>(null);
  const selectedLayer = layers.find((l) => l.id === selectedLayerId);

  const onPointerDown = (
    ev: ReactPointerEvent<HTMLDivElement>,
    layerId: string,
    handle: HandleId,
  ) => {
    ev.stopPropagation();
    const layer = layers.find((l) => l.id === layerId);
    if (!layer || layer.locked) return;
    setSelectedLayer(layerId);
    (ev.target as HTMLElement).setPointerCapture(ev.pointerId);
    dragRef.current = {
      layerId,
      handle,
      startX: ev.clientX,
      startY: ev.clientY,
      startRect: {
        x: layer.x,
        y: layer.y,
        w: layer.width,
        h: layer.height,
      },
      previewW: previewSize.w,
      previewH: previewSize.h,
    };
  };

  const onPointerMove = (ev: ReactPointerEvent<HTMLDivElement>) => {
    const d = dragRef.current;
    if (!d) return;
    const dx = (ev.clientX - d.startX) / d.previewW;
    const dy = (ev.clientY - d.startY) / d.previewH;
    let { x, y, w, h } = d.startRect;
    switch (d.handle) {
      case "move":
        x = Math.min(1, Math.max(0, x + dx));
        y = Math.min(1, Math.max(0, y + dy));
        // also clamp so layer stays within canvas
        x = Math.min(x, 1 - w);
        y = Math.min(y, 1 - h);
        break;
      case "e":
        w = Math.max(0.02, Math.min(1 - x, w + dx));
        break;
      case "w":
        w = Math.max(0.02, w - dx);
        x = Math.max(0, d.startRect.x + dx);
        if (x + w > 1) w = 1 - x;
        break;
      case "s":
        h = Math.max(0.02, Math.min(1 - y, h + dy));
        break;
      case "n":
        h = Math.max(0.02, h - dy);
        y = Math.max(0, d.startRect.y + dy);
        if (y + h > 1) h = 1 - y;
        break;
      case "se":
        w = Math.max(0.02, Math.min(1 - x, w + dx));
        h = Math.max(0.02, Math.min(1 - y, h + dy));
        break;
      case "sw":
        w = Math.max(0.02, w - dx);
        x = Math.max(0, d.startRect.x + dx);
        if (x + w > 1) w = 1 - x;
        h = Math.max(0.02, Math.min(1 - y, h + dy));
        break;
      case "ne":
        w = Math.max(0.02, Math.min(1 - x, w + dx));
        h = Math.max(0.02, h - dy);
        y = Math.max(0, d.startRect.y + dy);
        if (y + h > 1) h = 1 - y;
        break;
      case "nw":
        w = Math.max(0.02, w - dx);
        x = Math.max(0, d.startRect.x + dx);
        if (x + w > 1) w = 1 - x;
        h = Math.max(0.02, h - dy);
        y = Math.max(0, d.startRect.y + dy);
        if (y + h > 1) h = 1 - y;
        break;
    }
    updateLayer(d.layerId, { x, y, width: w, height: h });
  };

  const onPointerUp = () => {
    dragRef.current = null;
  };

  return (
    <div className="relative h-full w-full flex items-center justify-center p-4 select-none">
      <div
        ref={wrapRef}
        className="relative h-full w-full flex items-center justify-center"
      >
        <div
          className="relative rounded-lg overflow-hidden bg-black panel-shadow border border-[var(--color-border-hi)]"
          style={{ width: previewSize.w, height: previewSize.h }}
          onPointerDown={() => setSelectedLayer(null)}
        >
          <canvas
            ref={canvasRef}
            width={aspect.w}
            height={aspect.h}
            style={{
              width: "100%",
              height: "100%",
              display: "block",
              pointerEvents: "none",
            }}
          />
          {/* Layer overlay handles */}
          <div
            className="absolute inset-0"
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
          >
            {layers
              .filter((l) => l.visible && !l.locked && l.type !== "background" && l.type !== "effect")
              .map((l) => (
                <LayerHandle
                  key={l.id}
                  layer={l}
                  selected={selectedLayerId === l.id}
                  onPointerDown={onPointerDown}
                />
              ))}
          </div>
          {/* Aspect ratio chip */}
          <div className="absolute top-2 left-2 px-2 py-0.5 text-[10px] rounded bg-black/60 border border-white/10 text-white/80 font-mono">
            {aspect.id} • {aspect.w}×{aspect.h}
          </div>
          {selectedLayer && (
            <div className="absolute bottom-2 left-2 px-2 py-0.5 text-[10px] rounded bg-black/60 border border-white/10 text-white/80 font-mono">
              {selectedLayer.name} •{" "}
              {(selectedLayer.width * aspect.w).toFixed(0)}×
              {(selectedLayer.height * aspect.h).toFixed(0)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LayerHandle({
  layer,
  selected,
  onPointerDown,
}: {
  layer: Layer;
  selected: boolean;
  onPointerDown: (
    ev: ReactPointerEvent<HTMLDivElement>,
    layerId: string,
    handle: HandleId,
  ) => void;
}) {
  return (
    <div
      className="absolute"
      style={{
        left: `${layer.x * 100}%`,
        top: `${layer.y * 100}%`,
        width: `${layer.width * 100}%`,
        height: `${layer.height * 100}%`,
        cursor: "move",
        outline: selected ? "1px solid var(--color-accent)" : "1px dashed rgba(255,255,255,0.18)",
        outlineOffset: "-1px",
      }}
      onPointerDown={(e) => onPointerDown(e, layer.id, "move")}
    >
      {selected &&
        (["nw", "n", "ne", "w", "e", "sw", "s", "se"] as const).map((h) => (
          <div
            key={h}
            onPointerDown={(e) => onPointerDown(e, layer.id, h)}
            className="absolute w-2.5 h-2.5 bg-[var(--color-accent)] border border-white rounded-sm"
            style={handlePosStyle(h)}
          />
        ))}
    </div>
  );
}

function handlePosStyle(h: HandleId): React.CSSProperties {
  const offset = -5;
  switch (h) {
    case "nw":
      return { left: offset, top: offset, cursor: "nwse-resize" };
    case "n":
      return { left: "calc(50% - 5px)", top: offset, cursor: "ns-resize" };
    case "ne":
      return { right: offset, top: offset, cursor: "nesw-resize" };
    case "w":
      return { left: offset, top: "calc(50% - 5px)", cursor: "ew-resize" };
    case "e":
      return { right: offset, top: "calc(50% - 5px)", cursor: "ew-resize" };
    case "sw":
      return { left: offset, bottom: offset, cursor: "nesw-resize" };
    case "s":
      return { left: "calc(50% - 5px)", bottom: offset, cursor: "ns-resize" };
    case "se":
      return { right: offset, bottom: offset, cursor: "nwse-resize" };
    default:
      return {};
  }
}
