import { useStudio } from "@/store/studioStore";
import { ASPECT_RATIOS } from "@/data/aspectRatios";
import { AudioEngine } from "@/lib/audio/engine";
import {
  FileButton,
  IconBtn,
  Label,
  NumberRow,
  PanelSection,
  Toggle,
} from "@/components/ui/UI";
import { Play, Pause, Trash2, Music2 } from "lucide-react";
import { useEffect } from "react";

function formatTime(s: number) {
  if (!Number.isFinite(s)) return "0:00";
  const m = Math.floor(s / 60);
  const r = Math.floor(s % 60);
  return `${m}:${r.toString().padStart(2, "0")}`;
}

export function AudioPanel() {
  const aspect = useStudio((s) => s.aspect);
  const setAspect = useStudio((s) => s.setAspect);
  const tracks = useStudio((s) => s.tracks);
  const currentTrackId = useStudio((s) => s.currentTrackId);
  const addTracks = useStudio((s) => s.addTracks);
  const removeTrack = useStudio((s) => s.removeTrack);
  const setCurrentTrack = useStudio((s) => s.setCurrentTrack);
  const playing = useStudio((s) => s.playing);
  const currentTime = useStudio((s) => s.currentTime);
  const duration = useStudio((s) => s.duration);
  const beatSensitivity = useStudio((s) => s.beatSensitivity);
  const setBeatSensitivity = useStudio((s) => s.setBeatSensitivity);
  const loopPlaylist = useStudio((s) => s.loopPlaylist);
  const setLoopPlaylist = useStudio((s) => s.setLoopPlaylist);
  const detectedBpm = useStudio((s) => s.detectedBpm);
  const setExport = useStudio((s) => s.setExport);

  const current = tracks.find((t) => t.id === currentTrackId);

  // Wire audio engine to current track
  useEffect(() => {
    if (!current) return;
    AudioEngine.get().setSrc(current.url);
  }, [current]);

  // Track playing state of underlying audio
  useEffect(() => {
    const audio = AudioEngine.get().audio;
    const onPlay = () => useStudio.getState().setPlaying(true);
    const onPause = () => useStudio.getState().setPlaying(false);
    const onEnded = () => {
      const state = useStudio.getState();
      const idx = state.tracks.findIndex((t) => t.id === state.currentTrackId);
      if (idx < 0) return;
      const next = state.tracks[idx + 1];
      if (next) {
        state.setCurrentTrack(next.id);
        setTimeout(() => AudioEngine.get().play(), 0);
      } else if (state.loopPlaylist && state.tracks[0]) {
        state.setCurrentTrack(state.tracks[0].id);
        setTimeout(() => AudioEngine.get().play(), 0);
      } else {
        state.setPlaying(false);
      }
    };
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("ended", onEnded);
    return () => {
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("ended", onEnded);
    };
  }, []);

  const togglePlay = async () => {
    if (!current) return;
    if (playing) AudioEngine.get().pause();
    else await AudioEngine.get().play();
  };

  return (
    <>
      <PanelSection title="Aspect Ratio">
        <Label>Output canvas</Label>
        <div className="grid grid-cols-2 gap-2">
          {ASPECT_RATIOS.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => {
                setAspect(a.id);
                setExport({ width: a.w, height: a.h });
              }}
              className={`px-3 py-2 rounded-md text-xs border ${
                aspect.id === a.id
                  ? "border-[var(--color-accent)] bg-[var(--color-accent)]/20 text-white"
                  : "border-[var(--color-border)] bg-[var(--color-bg-3)] text-[var(--color-text-muted)] hover:text-white"
              }`}
            >
              <div className="font-semibold">{a.id}</div>
              <div className="text-[10px] opacity-70 mt-0.5">
                {a.w}×{a.h}
              </div>
            </button>
          ))}
        </div>
      </PanelSection>

      <PanelSection title="Music / Audio Files">
        <FileButton
          accept="audio/*"
          multiple
          onPick={(files) => addTracks(files)}
        >
          <Music2 size={14} /> Add Audio
        </FileButton>
        <div className="space-y-1.5 mt-2">
          {tracks.length === 0 ? (
            <p className="text-[11px] text-[var(--color-text-muted)]">
              No audio added. Add one or more audio files to play and visualize.
            </p>
          ) : (
            tracks.map((t) => (
              <div
                key={t.id}
                className={`flex items-center gap-2 px-2.5 py-2 rounded-md text-xs ${
                  t.id === currentTrackId
                    ? "bg-[var(--color-bg-3)] ring-1 ring-[var(--color-accent)]"
                    : "bg-[var(--color-bg-3)]/40 hover:bg-[var(--color-bg-3)]"
                }`}
              >
                <button
                  type="button"
                  onClick={async () => {
                    setCurrentTrack(t.id);
                    setTimeout(() => AudioEngine.get().play(), 50);
                  }}
                  className="text-[var(--color-text-muted)] hover:text-white"
                >
                  <Play size={12} />
                </button>
                <span className="truncate flex-1">{t.name}</span>
                <span className="text-[10px] tabular-nums text-[var(--color-text-muted)]">
                  {formatTime(t.duration)}
                </span>
                <IconBtn
                  title="Remove"
                  onClick={() => removeTrack(t.id)}
                  danger
                >
                  <Trash2 size={12} />
                </IconBtn>
              </div>
            ))
          )}
        </div>
      </PanelSection>

      <PanelSection title="Playback">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={togglePlay}
            disabled={!current}
            className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-[var(--color-accent)] hover:bg-[var(--color-accent-hi)] disabled:opacity-40 text-white"
          >
            {playing ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <div className="flex-1">
            <input
              type="range"
              min={0}
              max={duration || 0}
              value={currentTime}
              step={0.01}
              onChange={(e) => AudioEngine.get().seek(Number(e.target.value))}
            />
            <div className="flex justify-between text-[10px] text-[var(--color-text-muted)] tabular-nums mt-1">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>
        </div>
        <Toggle
          label="Loop playlist"
          checked={loopPlaylist}
          onChange={setLoopPlaylist}
        />
      </PanelSection>

      <PanelSection title="Beat Detection">
        <NumberRow
          label="Beat Sensitivity"
          value={beatSensitivity}
          min={0.05}
          max={1}
          step={0.01}
          onChange={setBeatSensitivity}
        />
        <div className="flex items-center justify-between text-xs">
          <span className="text-[var(--color-text-muted)]">Detected BPM</span>
          <span className="font-mono tabular-nums">
            {detectedBpm ? detectedBpm.toFixed(1) : "—"}
          </span>
        </div>
        <p className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">
          Beat-zoom for images, text and lyrics uses the live beat detected from
          the audio (bass-band onset detection). Higher sensitivity catches more
          beats — including softer ones.
        </p>
      </PanelSection>

      <div className="h-2" />
    </>
  );
}
