import { useStudio } from "@/store/studioStore";
import { VISUALIZER_GENRES, VISUALIZER_PRESETS } from "@/data/visualizers";
import {
  ColorInput,
  Label,
  NumberRow,
  PanelSection,
  Toggle,
} from "@/components/ui/UI";
import type { VisualizerLayer } from "@/types/studio";
import { useMemo, useState } from "react";

export function VisualizerPanel() {
  const addVisualizerLayer = useStudio((s) => s.addVisualizerLayer);
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const updateLayer = useStudio((s) => s.updateLayer);
  const [filterGenre, setFilterGenre] = useState<string>("all");

  const selected = layers.find(
    (l): l is VisualizerLayer =>
      l.type === "visualizer" && l.id === selectedLayerId,
  );

  const filtered = useMemo(
    () =>
      filterGenre === "all"
        ? VISUALIZER_PRESETS
        : VISUALIZER_PRESETS.filter((p) => p.genre === filterGenre),
    [filterGenre],
  );

  return (
    <>
      <PanelSection title="Spectrum Library">
        <div className="flex flex-wrap gap-1 mb-2">
          <FilterChip
            label="All"
            active={filterGenre === "all"}
            onClick={() => setFilterGenre("all")}
          />
          {VISUALIZER_GENRES.map((g) => (
            <FilterChip
              key={g.id}
              label={g.label}
              active={filterGenre === g.id}
              onClick={() => setFilterGenre(g.id)}
            />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2">
          {filtered.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => addVisualizerLayer(p.id)}
              className="group relative rounded-md overflow-hidden border border-[var(--color-border)] hover:border-[var(--color-accent)] bg-[var(--color-bg-3)] text-left"
              title={`Add ${p.name}`}
            >
              <div
                className="h-16 w-full"
                style={{
                  background: `linear-gradient(135deg, ${p.colorA}, ${p.colorB})`,
                }}
              />
              <div className="px-2 py-1.5">
                <div className="text-[11px] font-semibold truncate">
                  {p.name}
                </div>
                <div className="text-[10px] text-[var(--color-text-muted)] capitalize">
                  {p.style.replace("-", " ")}
                </div>
              </div>
            </button>
          ))}
        </div>
      </PanelSection>

      {selected && (
        <PanelSection title={`${selected.name} — Settings`}>
          <Label>Color A</Label>
          <ColorInput
            value={selected.colorA ?? "#7c5cff"}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { colorA: v })
            }
          />
          <Label>Color B</Label>
          <ColorInput
            value={selected.colorB ?? "#21d4fd"}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { colorB: v })
            }
          />
          <NumberRow
            label="Bar count"
            value={selected.bars ?? 64}
            min={8}
            max={192}
            step={2}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { bars: v })
            }
          />
          <NumberRow
            label="Thickness"
            value={selected.thickness ?? 4}
            min={1}
            max={24}
            step={1}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { thickness: v })
            }
          />
          <NumberRow
            label="Glow"
            value={selected.glow ?? 0.7}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { glow: v })
            }
          />
          <NumberRow
            label="Opacity"
            value={selected.opacity}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { opacity: v })
            }
          />
          <Toggle
            label="Mirror"
            checked={!!selected.mirror}
            onChange={(v) =>
              updateLayer<VisualizerLayer>(selected.id, { mirror: v })
            }
          />
        </PanelSection>
      )}
    </>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-2 py-0.5 rounded-full text-[10px] border ${
        active
          ? "bg-[var(--color-accent)] border-[var(--color-accent)] text-white"
          : "bg-[var(--color-bg-3)] border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-white"
      }`}
    >
      {label}
    </button>
  );
}
