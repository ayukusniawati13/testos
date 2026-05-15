import { useEffect } from "react";
import { useStudio } from "@/store/studioStore";
import {
  ButtonGroup,
  FileButton,
  IconBtn,
  Label,
  NumberRow,
  PanelSection,
} from "@/components/ui/UI";
import type { BackgroundLayer } from "@/types/studio";
import { ImagePlus, Trash2 } from "lucide-react";

export function BackgroundPanel() {
  const layers = useStudio((s) => s.layers);
  const addBackgroundLayer = useStudio((s) => s.addBackgroundLayer);
  const addBackgroundItems = useStudio((s) => s.addBackgroundItems);
  const removeBackgroundItem = useStudio((s) => s.removeBackgroundItem);
  const updateLayer = useStudio((s) => s.updateLayer);

  const bg = layers.find((l): l is BackgroundLayer => l.type === "background");

  // Auto-create a background layer when this panel opens
  useEffect(() => {
    if (!bg) addBackgroundLayer();
  }, [bg, addBackgroundLayer]);

  if (!bg) return null;

  return (
    <>
      <PanelSection title="Background Media">
        <FileButton
          accept="image/*,video/*"
          multiple
          onPick={(files) => addBackgroundItems(bg.id, files)}
        >
          <ImagePlus size={14} /> Add Image / Video
        </FileButton>
        <div className="space-y-1.5 mt-2">
          {bg.items.length === 0 ? (
            <p className="text-[11px] text-[var(--color-text-muted)]">
              No backgrounds added. Upload images or videos — multiple files
              will auto-cycle with a smooth crossfade.
            </p>
          ) : (
            bg.items.map((it) => (
              <div
                key={it.id}
                className="flex items-center gap-2 px-2.5 py-2 rounded-md text-xs bg-[var(--color-bg-3)]/40"
              >
                {it.kind === "image" ? (
                  <img
                    src={it.src}
                    alt=""
                    className="w-8 h-8 rounded object-cover"
                  />
                ) : (
                  <video
                    src={it.src}
                    muted
                    className="w-8 h-8 rounded object-cover bg-black"
                  />
                )}
                <span className="truncate flex-1">{it.fileName}</span>
                <span className="text-[10px] uppercase opacity-60">
                  {it.kind}
                </span>
                <IconBtn
                  title="Remove"
                  onClick={() => removeBackgroundItem(bg.id, it.id)}
                  danger
                >
                  <Trash2 size={12} />
                </IconBtn>
              </div>
            ))
          )}
        </div>
      </PanelSection>
      <PanelSection title="Slideshow & Effects">
        <NumberRow
          label="Time per item"
          value={bg.intervalSec}
          min={1}
          max={30}
          step={0.5}
          suffix="s"
          onChange={(v) =>
            updateLayer<BackgroundLayer>(bg.id, { intervalSec: v })
          }
        />
        <NumberRow
          label="Crossfade duration"
          value={bg.crossfadeSec}
          min={0.1}
          max={5}
          step={0.1}
          suffix="s"
          onChange={(v) =>
            updateLayer<BackgroundLayer>(bg.id, { crossfadeSec: v })
          }
        />
        <NumberRow
          label="Blur"
          value={bg.blur}
          min={0}
          max={40}
          step={1}
          onChange={(v) => updateLayer<BackgroundLayer>(bg.id, { blur: v })}
        />
        <NumberRow
          label="Brightness"
          value={bg.brightness}
          min={0.1}
          max={2}
          step={0.05}
          onChange={(v) =>
            updateLayer<BackgroundLayer>(bg.id, { brightness: v })
          }
        />
        <Label>Fit mode</Label>
        <ButtonGroup
          value={bg.fit}
          onChange={(v) => updateLayer<BackgroundLayer>(bg.id, { fit: v })}
          options={[
            { value: "cover", label: "Cover" },
            { value: "contain", label: "Contain" },
            { value: "fill", label: "Fill" },
          ]}
        />
        <NumberRow
          label="Opacity"
          value={bg.opacity}
          min={0}
          max={1}
          step={0.01}
          onChange={(v) => updateLayer<BackgroundLayer>(bg.id, { opacity: v })}
        />
      </PanelSection>
    </>
  );
}
