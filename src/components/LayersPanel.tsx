import { useStudio } from "@/store/studioStore";
import {
  ChevronUp,
  ChevronDown,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Trash2,
  Image as ImageIcon,
  Type,
  AudioLines,
  Layers as LayersIcon,
  Wand2,
  ImagePlay,
  Sparkles,
} from "lucide-react";
import type { Layer } from "@/types/studio";

const LAYER_ICONS: Record<Layer["type"], typeof ImageIcon> = {
  background: ImagePlay,
  visualizer: AudioLines,
  image: ImageIcon,
  text: Type,
  lyrics: Sparkles,
  effect: Wand2,
};

export function LayersPanel() {
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const setSelectedLayer = useStudio((s) => s.setSelectedLayer);
  const toggleVisible = useStudio((s) => s.toggleLayerVisible);
  const toggleLocked = useStudio((s) => s.toggleLayerLocked);
  const moveLayer = useStudio((s) => s.moveLayer);
  const removeLayer = useStudio((s) => s.removeLayer);

  // Display top-to-bottom in z-order (last rendered = top, so reverse)
  const display = [...layers].reverse();

  return (
    <aside className="w-64 shrink-0 bg-[var(--color-bg-1)] border-r border-[var(--color-border)] flex flex-col">
      <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LayersIcon size={16} className="text-[var(--color-accent)]" />
          <span className="text-sm font-semibold">Layers</span>
        </div>
        <span className="text-[11px] text-[var(--color-text-muted)]">
          {layers.length}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto">
        {display.length === 0 ? (
          <div className="px-4 py-6 text-xs text-[var(--color-text-muted)] text-center">
            No layers yet. Use the menu on the right to add Background, Images,
            Visualizers, Text, Lyrics, or Effects.
          </div>
        ) : (
          <ul className="py-1">
            {display.map((l) => {
              const Icon = LAYER_ICONS[l.type];
              const selected = l.id === selectedLayerId;
              return (
                <li
                  key={l.id}
                  className={`group flex items-center gap-2 px-3 py-2 mx-1 my-0.5 rounded-md cursor-pointer ${
                    selected
                      ? "bg-[var(--color-bg-3)] ring-1 ring-[var(--color-accent)]"
                      : "hover:bg-[var(--color-bg-2)]"
                  }`}
                  onClick={() => setSelectedLayer(l.id)}
                >
                  <Icon size={14} className="text-[var(--color-text-muted)] shrink-0" />
                  <span className="text-xs truncate flex-1">{l.name}</span>
                  <div className="flex items-center gap-0.5 opacity-60 group-hover:opacity-100">
                    <button
                      type="button"
                      title="Move up"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveLayer(l.id, 1);
                      }}
                      className="p-1 hover:text-white text-[var(--color-text-muted)]"
                    >
                      <ChevronUp size={13} />
                    </button>
                    <button
                      type="button"
                      title="Move down"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveLayer(l.id, -1);
                      }}
                      className="p-1 hover:text-white text-[var(--color-text-muted)]"
                    >
                      <ChevronDown size={13} />
                    </button>
                    <button
                      type="button"
                      title={l.visible ? "Hide" : "Show"}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleVisible(l.id);
                      }}
                      className="p-1 hover:text-white text-[var(--color-text-muted)]"
                    >
                      {l.visible ? <Eye size={13} /> : <EyeOff size={13} />}
                    </button>
                    <button
                      type="button"
                      title={l.locked ? "Unlock" : "Lock"}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleLocked(l.id);
                      }}
                      className="p-1 hover:text-white text-[var(--color-text-muted)]"
                    >
                      {l.locked ? <Lock size={13} /> : <Unlock size={13} />}
                    </button>
                    <button
                      type="button"
                      title="Delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeLayer(l.id);
                      }}
                      className="p-1 hover:text-[var(--color-danger)] text-[var(--color-text-muted)]"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
