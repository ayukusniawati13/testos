import { useState } from "react";
import { useStudio } from "@/store/studioStore";
import {
  ButtonGroup,
  ColorInput,
  IconBtn,
  Label,
  NumberRow,
  PanelSection,
  Select,
  TextInput,
  Toggle,
} from "@/components/ui/UI";
import { FONT_OPTIONS } from "@/data/fonts";
import type { LyricLine, LyricsLayer } from "@/types/studio";
import { Key, Plus, Sparkles, Trash2, Wand2 } from "lucide-react";
import { transcribeWithGroq } from "@/lib/groq";

export function LyricsPanel() {
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const addLyricsLayer = useStudio((s) => s.addLyricsLayer);
  const removeLayer = useStudio((s) => s.removeLayer);
  const updateLayer = useStudio((s) => s.updateLayer);
  const setSelectedLayer = useStudio((s) => s.setSelectedLayer);
  const setLyrics = useStudio((s) => s.setLyrics);
  const groqKeys = useStudio((s) => s.groqKeys);
  const addGroqKey = useStudio((s) => s.addGroqKey);
  const removeGroqKey = useStudio((s) => s.removeGroqKey);
  const tracks = useStudio((s) => s.tracks);
  const currentTrackId = useStudio((s) => s.currentTrackId);

  const [newKeyName, setNewKeyName] = useState("");
  const [newKey, setNewKey] = useState("");
  const [activeKeyId, setActiveKeyId] = useState<string>("");
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lyricsLayers = layers.filter(
    (l): l is LyricsLayer => l.type === "lyrics",
  );

  const handleTranscribe = async (layerId: string) => {
    setError(null);
    const track = tracks.find((t) => t.id === currentTrackId) ?? tracks[0];
    if (!track) {
      setError("Add an audio file in the Audio menu first.");
      return;
    }
    const key = groqKeys.find((k) => k.id === activeKeyId) ?? groqKeys[0];
    if (!key) {
      setError("Add at least one Groq API key first.");
      return;
    }
    setTranscribing(true);
    try {
      const lines = await transcribeWithGroq(key.key, track.file);
      setLyrics(layerId, lines);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTranscribing(false);
    }
  };

  return (
    <>
      <PanelSection title="Groq AI API Keys">
        <div className="space-y-2">
          {groqKeys.length === 0 ? (
            <p className="text-[11px] text-[var(--color-text-muted)]">
              Add one or more Groq API keys. They are kept only in memory in
              this session (never sent to a server) and used for AI lyric
              transcription with Whisper.
            </p>
          ) : (
            groqKeys.map((k) => (
              <div
                key={k.id}
                className="flex items-center gap-2 px-2.5 py-2 rounded-md text-xs bg-[var(--color-bg-3)]/40"
              >
                <Key
                  size={12}
                  className={
                    activeKeyId === k.id
                      ? "text-[var(--color-accent)]"
                      : "text-[var(--color-text-muted)]"
                  }
                />
                <button
                  type="button"
                  onClick={() => setActiveKeyId(k.id)}
                  className="truncate flex-1 text-left"
                >
                  {k.name}
                </button>
                <span className="text-[10px] font-mono text-[var(--color-text-muted)]">
                  ····{k.key.slice(-4)}
                </span>
                <IconBtn
                  title="Remove key"
                  onClick={() => removeGroqKey(k.id)}
                  danger
                >
                  <Trash2 size={12} />
                </IconBtn>
              </div>
            ))
          )}
        </div>
        <div className="space-y-2 pt-2 border-t border-[var(--color-border)]">
          <Label>Add key</Label>
          <TextInput
            value={newKeyName}
            onChange={setNewKeyName}
            placeholder="Key name (e.g. Personal)"
          />
          <TextInput
            value={newKey}
            onChange={setNewKey}
            placeholder="gsk_..."
            type="password"
          />
          <button
            type="button"
            disabled={!newKey || !newKeyName}
            onClick={() => {
              addGroqKey(newKeyName, newKey);
              setNewKeyName("");
              setNewKey("");
            }}
            className="inline-flex items-center justify-center gap-2 px-3 py-2 w-full rounded-md text-sm bg-[var(--color-accent)] hover:bg-[var(--color-accent-hi)] disabled:opacity-40 text-white"
          >
            <Plus size={14} /> Add API Key
          </button>
        </div>
      </PanelSection>

      <PanelSection title="Lyric Layers">
        <button
          type="button"
          onClick={addLyricsLayer}
          className="inline-flex items-center justify-center gap-2 px-3 py-2 w-full rounded-md text-sm bg-[var(--color-accent)] hover:bg-[var(--color-accent-hi)] text-white"
        >
          <Sparkles size={14} /> Add Lyrics Layer
        </button>
        {error && (
          <p className="text-[11px] text-[var(--color-danger)]">{error}</p>
        )}
        <div className="space-y-1.5 mt-2">
          {lyricsLayers.map((l) => (
            <button
              key={l.id}
              type="button"
              onClick={() => setSelectedLayer(l.id)}
              className={`flex items-center gap-2 px-2.5 py-2 w-full rounded-md text-xs ${
                l.id === selectedLayerId
                  ? "bg-[var(--color-bg-3)] ring-1 ring-[var(--color-accent)]"
                  : "bg-[var(--color-bg-3)]/40 hover:bg-[var(--color-bg-3)]"
              }`}
            >
              <Sparkles size={12} className="text-[var(--color-accent)]" />
              <span className="truncate flex-1 text-left">{l.name}</span>
              <span className="text-[10px] text-[var(--color-text-muted)]">
                {l.lines.length} lines
              </span>
              <IconBtn title="Remove" onClick={() => removeLayer(l.id)} danger>
                <Trash2 size={12} />
              </IconBtn>
            </button>
          ))}
        </div>
      </PanelSection>

      {lyricsLayers.map((l) => (
        <PanelSection
          key={l.id}
          title={`${l.name} — Settings`}
          defaultOpen={l.id === selectedLayerId}
        >
          <button
            type="button"
            onClick={() => handleTranscribe(l.id)}
            disabled={transcribing || groqKeys.length === 0}
            className="inline-flex items-center justify-center gap-2 px-3 py-2 w-full rounded-md text-sm bg-[var(--color-bg-3)] hover:bg-[var(--color-bg-2)] border border-[var(--color-border-hi)] disabled:opacity-40 text-white"
          >
            <Wand2 size={14} />
            {transcribing ? "Transcribing…" : "Auto-generate from audio (Groq)"}
          </button>

          <Label>Font</Label>
          <Select
            value={l.fontFamily}
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { fontFamily: v })}
            options={FONT_OPTIONS.map((f) => ({
              value: f.family,
              label: f.label,
            }))}
          />
          <NumberRow
            label="Font size"
            value={l.fontSize}
            min={20}
            max={220}
            step={1}
            suffix="px"
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { fontSize: v })}
          />
          <Label>Weight</Label>
          <ButtonGroup
            value={String(l.fontWeight) as "300" | "400" | "500" | "600" | "700" | "800"}
            onChange={(v) =>
              updateLayer<LyricsLayer>(l.id, {
                fontWeight: Number(v) as LyricsLayer["fontWeight"],
              })
            }
            options={[
              { value: "300", label: "Light" },
              { value: "400", label: "Reg" },
              { value: "700", label: "Bold" },
              { value: "800", label: "X-Bold" },
            ]}
            size="sm"
          />
          <Toggle
            label="Italic"
            checked={l.italic}
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { italic: v })}
          />
          <Label>Lyric style</Label>
          <ButtonGroup
            value={l.style}
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { style: v })}
            options={[
              { value: "plain", label: "Plain" },
              { value: "neon", label: "Neon" },
              { value: "outline", label: "Outline" },
              { value: "gradient", label: "Gradient" },
              { value: "chrome", label: "Chrome" },
            ]}
            size="sm"
          />
          <Label>Animation</Label>
          <Select
            value={l.animation}
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { animation: v })}
            options={[
              { value: "fade", label: "Fade" },
              { value: "typewriter", label: "Typewriter" },
              { value: "slide-up", label: "Slide Up" },
              { value: "scale-pop", label: "Scale Pop" },
              { value: "neon-glow", label: "Neon Glow" },
              { value: "bounce", label: "Bounce" },
              { value: "karaoke", label: "Karaoke" },
            ]}
          />
          <Label>Color</Label>
          <ColorInput
            value={l.color}
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { color: v })}
          />
          <Label>Highlight color</Label>
          <ColorInput
            value={l.highlightColor}
            onChange={(v) =>
              updateLayer<LyricsLayer>(l.id, { highlightColor: v })
            }
          />
          <Toggle
            label="Beat zoom"
            checked={l.beatZoom}
            onChange={(v) => updateLayer<LyricsLayer>(l.id, { beatZoom: v })}
          />
          {l.beatZoom && (
            <NumberRow
              label="Zoom amount"
              value={l.beatZoomAmount}
              min={0.02}
              max={0.6}
              step={0.01}
              onChange={(v) =>
                updateLayer<LyricsLayer>(l.id, { beatZoomAmount: v })
              }
            />
          )}
          <LyricsEditor layer={l} />
        </PanelSection>
      ))}
    </>
  );
}

function LyricsEditor({ layer }: { layer: LyricsLayer }) {
  const setLyrics = useStudio((s) => s.setLyrics);
  const [text, setText] = useState(() =>
    layer.lines
      .map(
        (l) =>
          `[${formatTC(l.time)}] ${l.text} (${l.duration.toFixed(2)}s)`,
      )
      .join("\n"),
  );

  function parse(): LyricLine[] {
    const lines: LyricLine[] = [];
    for (const raw of text.split(/\r?\n/)) {
      const m = raw.match(
        /^\s*\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*?)\s*(?:\((\d+(?:\.\d+)?)s\))?\s*$/,
      );
      if (!m) continue;
      const time = Number(m[1]) * 60 + Number(m[2]);
      const txt = m[3].trim();
      const dur = m[4] ? Number(m[4]) : 3;
      if (!txt) continue;
      lines.push({ time, text: txt, duration: dur });
    }
    return lines;
  }

  return (
    <>
      <Label>Lyric lines</Label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={6}
        placeholder="[0:00] First line (2.5s)&#10;[0:03] Second line (3s)"
        className="w-full px-3 py-2 rounded-md text-xs font-mono bg-[var(--color-bg-3)] border border-[var(--color-border)] focus:border-[var(--color-accent)] outline-none"
      />
      <button
        type="button"
        onClick={() => setLyrics(layer.id, parse())}
        className="px-3 py-1.5 rounded-md text-xs bg-[var(--color-bg-3)] hover:bg-[var(--color-bg-2)] border border-[var(--color-border-hi)] text-white"
      >
        Apply changes
      </button>
    </>
  );
}

function formatTC(t: number) {
  const m = Math.floor(t / 60);
  const s = (t - m * 60).toFixed(2);
  return `${m}:${s.padStart(5, "0")}`;
}
