import { useEffect, useRef, useState } from "react";
import { useStudio } from "@/store/studioStore";
import {
  ButtonGroup,
  Label,
  NumberRow,
  PanelSection,
  Toggle,
} from "@/components/ui/UI";
import type { ExportSettings } from "@/types/studio";
import { startExport, type ExportHandle } from "@/lib/export/exporter";
import { Square, Video } from "lucide-react";

const RESOLUTION_PRESETS: { label: string; w: number; h: number }[] = [
  { label: "1080p (1920×1080)", w: 1920, h: 1080 },
  { label: "1080p Vertical (1080×1920)", w: 1080, h: 1920 },
  { label: "Square 1080 (1080×1080)", w: 1080, h: 1080 },
  { label: "4K (3840×2160)", w: 3840, h: 2160 },
  { label: "720p (1280×720)", w: 1280, h: 720 },
];

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const r = Math.floor(s % 60);
  return `${m}:${r.toString().padStart(2, "0")}`;
}

export function ExportPanel() {
  const settings = useStudio((s) => s.exportSettings);
  const setExport = useStudio((s) => s.setExport);
  const aspect = useStudio((s) => s.aspect);
  const duration = useStudio((s) => s.duration);
  const [recording, setRecording] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [stopOnAudioEnd, setStopOnAudioEnd] = useState(true);
  const handleRef = useRef<ExportHandle | null>(null);

  // Keep export resolution in sync with chosen aspect by default
  useEffect(() => {
    setExport({ width: aspect.w, height: aspect.h });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aspect.id]);

  const start = () => {
    setError(null);
    // Use the actual on-screen preview canvas for capture (it renders at full
    // canvasW/H regardless of CSS size)
    const canvas =
      document.querySelector<HTMLCanvasElement>("canvas[data-preview]") ||
      document.querySelector<HTMLCanvasElement>("canvas");
    if (!canvas) {
      setError("Preview canvas not found.");
      return;
    }
    setRecording(true);
    setProgress(0);
    try {
      handleRef.current = startExport({
        canvas,
        fps: settings.fps,
        bitrateMbps: settings.bitrateMbps,
        format: settings.format,
        stopOnAudioEnd,
        onProgress: (s) => setProgress(s),
      });
      handleRef.current.promise
        .catch((e) => setError(e instanceof Error ? e.message : String(e)))
        .finally(() => {
          setRecording(false);
          handleRef.current = null;
        });
    } catch (e) {
      setRecording(false);
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const stop = () => {
    handleRef.current?.stop();
  };

  return (
    <>
      <PanelSection title="Resolution">
        <Label>Preset</Label>
        <div className="grid grid-cols-1 gap-1.5">
          {RESOLUTION_PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => setExport({ width: p.w, height: p.h })}
              className={`px-3 py-2 rounded-md text-xs border text-left ${
                settings.width === p.w && settings.height === p.h
                  ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-white"
                  : "border-[var(--color-border)] bg-[var(--color-bg-3)] text-[var(--color-text-muted)] hover:text-white"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        <p className="text-[11px] text-[var(--color-text-muted)] mt-1">
          Note: video is captured directly from the live preview canvas at the
          chosen aspect ratio. Pick the aspect in the Audio menu, then the
          resolution here.
        </p>
      </PanelSection>

      <PanelSection title="Quality">
        <Label>Frame rate</Label>
        <ButtonGroup
          value={String(settings.fps) as "24" | "30" | "60"}
          onChange={(v) =>
            setExport({ fps: Number(v) as ExportSettings["fps"] })
          }
          options={[
            { value: "24", label: "24" },
            { value: "30", label: "30" },
            { value: "60", label: "60" },
          ]}
        />
        <NumberRow
          label="Bitrate"
          value={settings.bitrateMbps}
          min={2}
          max={40}
          step={1}
          suffix=" Mbps"
          onChange={(v) => setExport({ bitrateMbps: v })}
        />
        <Label>Format</Label>
        <ButtonGroup
          value={settings.format}
          onChange={(v) => setExport({ format: v })}
          options={[
            { value: "webm", label: "WebM" },
            { value: "mp4", label: "MP4 (if supported)" },
          ]}
        />
      </PanelSection>

      <PanelSection title="Record">
        <Toggle
          label="Stop automatically when audio ends"
          checked={stopOnAudioEnd}
          onChange={setStopOnAudioEnd}
        />
        {!recording ? (
          <button
            type="button"
            onClick={start}
            className="inline-flex items-center justify-center gap-2 px-3 py-2.5 w-full rounded-md text-sm bg-[var(--color-danger)] hover:brightness-110 text-white font-semibold"
          >
            <Video size={14} /> Start Recording & Export
          </button>
        ) : (
          <button
            type="button"
            onClick={stop}
            className="inline-flex items-center justify-center gap-2 px-3 py-2.5 w-full rounded-md text-sm bg-[var(--color-bg-3)] border border-[var(--color-border-hi)] hover:bg-[var(--color-bg-2)] text-white font-semibold animate-pulse-soft"
          >
            <Square size={14} /> Stop ({formatTime(progress)}{" "}
            {duration ? `/ ${formatTime(duration)}` : ""})
          </button>
        )}
        {error && (
          <p className="text-[11px] text-[var(--color-danger)]">{error}</p>
        )}
        <p className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">
          Export uses the browser's native MediaRecorder — the video is captured
          in real-time from the preview, exactly as it appears on screen. The
          file will be downloaded automatically when recording stops.
        </p>
      </PanelSection>
    </>
  );
}
