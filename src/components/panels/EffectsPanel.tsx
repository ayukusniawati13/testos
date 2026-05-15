import { useMemo, useState } from "react";
import { useStudio } from "@/store/studioStore";
import { EFFECT_GENRES, EFFECT_PRESETS } from "@/data/effects";
import {
  ColorInput,
  NumberRow,
  PanelSection,
  Toggle,
} from "@/components/ui/UI";
import type { EffectLayer } from "@/types/studio";

export function EffectsPanel() {
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const addEffectLayer = useStudio((s) => s.addEffectLayer);
  const updateLayer = useStudio((s) => s.updateLayer);
  const [genreFilter, setGenreFilter] = useState<string>("all");

  const selected = layers.find(
    (l): l is EffectLayer => l.type === "effect" && l.id === selectedLayerId,
  );

  const filtered = useMemo(
    () =>
      genreFilter === "all"
        ? EFFECT_PRESETS
        : EFFECT_PRESETS.filter((p) => p.genre === genreFilter),
    [genreFilter],
  );

  return (
    <>
      <PanelSection title="Effects Library">
        <div className="flex flex-wrap gap-1 mb-2">
          <Chip
            label="All"
            active={genreFilter === "all"}
            onClick={() => setGenreFilter("all")}
          />
          {EFFECT_GENRES.map((g) => (
            <Chip
              key={g.id}
              label={g.label}
              active={genreFilter === g.id}
              onClick={() => setGenreFilter(g.id)}
            />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-2">
          {filtered.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => addEffectLayer(p.id)}
              className="text-left px-2 py-2 rounded-md border border-[var(--color-border)] hover:border-[var(--color-accent)] bg-[var(--color-bg-3)]"
            >
              <div className="text-[11px] font-semibold truncate">
                {p.name}
              </div>
              <div className="text-[10px] text-[var(--color-text-muted)] capitalize">
                {p.kind.replace("-", " ")}
              </div>
            </button>
          ))}
        </div>
      </PanelSection>

      {selected && (
        <PanelSection title={`${selected.name} — Settings`}>
          <NumberRow
            label="Intensity"
            value={selected.intensity}
            min={0.05}
            max={1}
            step={0.01}
            onChange={(v) =>
              updateLayer<EffectLayer>(selected.id, { intensity: v })
            }
          />
          <NumberRow
            label="Speed"
            value={selected.speed}
            min={0.1}
            max={3}
            step={0.05}
            onChange={(v) =>
              updateLayer<EffectLayer>(selected.id, { speed: v })
            }
          />
          <NumberRow
            label="Opacity"
            value={selected.opacity}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) =>
              updateLayer<EffectLayer>(selected.id, { opacity: v })
            }
          />
          <Toggle
            label="Beat reactive"
            checked={selected.beatReactive}
            onChange={(v) =>
              updateLayer<EffectLayer>(selected.id, { beatReactive: v })
            }
          />
          <ColorInput
            value={selected.color ?? "#ffffff"}
            onChange={(v) =>
              updateLayer<EffectLayer>(selected.id, { color: v })
            }
          />
        </PanelSection>
      )}
    </>
  );
}

function Chip({
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
