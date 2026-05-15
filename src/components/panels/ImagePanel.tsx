import { useStudio } from "@/store/studioStore";
import {
  ButtonGroup,
  ColorInput,
  FileButton,
  IconBtn,
  Label,
  NumberRow,
  PanelSection,
  Toggle,
} from "@/components/ui/UI";
import type { ImageLayer } from "@/types/studio";
import { ImagePlus, Trash2 } from "lucide-react";

export function ImagePanel() {
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const addImageLayer = useStudio((s) => s.addImageLayer);
  const removeLayer = useStudio((s) => s.removeLayer);
  const updateLayer = useStudio((s) => s.updateLayer);
  const setSelectedLayer = useStudio((s) => s.setSelectedLayer);

  const imageLayers = layers.filter(
    (l): l is ImageLayer => l.type === "image",
  );

  return (
    <>
      <PanelSection title="Images / Logos">
        <FileButton
          accept="image/*"
          multiple
          onPick={async (files) => {
            for (const f of files) await addImageLayer(f);
          }}
        >
          <ImagePlus size={14} /> Add Image
        </FileButton>
        <div className="space-y-1.5 mt-2">
          {imageLayers.length === 0 ? (
            <p className="text-[11px] text-[var(--color-text-muted)]">
              No images added yet. Add one or more — each image has its own
              settings (shape, rotation, transparency, beat zoom, outline).
            </p>
          ) : (
            imageLayers.map((l) => (
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
                <img
                  src={l.src}
                  alt=""
                  className="w-7 h-7 rounded object-cover border border-[var(--color-border)]"
                />
                <span className="truncate flex-1 text-left">{l.fileName}</span>
                <IconBtn
                  title="Remove"
                  onClick={() => removeLayer(l.id)}
                  danger
                >
                  <Trash2 size={12} />
                </IconBtn>
              </button>
            ))
          )}
        </div>
      </PanelSection>

      {imageLayers.map((l) => (
        <PanelSection
          key={l.id}
          title={l.name + " — Settings"}
          defaultOpen={l.id === selectedLayerId}
        >
          <Label>Shape mode</Label>
          <ButtonGroup
            value={l.shape}
            onChange={(v) => updateLayer<ImageLayer>(l.id, { shape: v })}
            options={[
              { value: "original", label: "Original" },
              { value: "rounded", label: "Rounded" },
              { value: "circle", label: "Circle" },
            ]}
          />

          <Label>Image mode (rotation)</Label>
          <ButtonGroup
            value={l.rotateMode}
            onChange={(v) => updateLayer<ImageLayer>(l.id, { rotateMode: v })}
            options={[
              { value: "none", label: "Static" },
              { value: "ccw", label: "Left" },
              { value: "cw", label: "Right" },
            ]}
          />
          {l.rotateMode !== "none" && (
            <NumberRow
              label="Rotation speed"
              value={l.rotateSpeed}
              min={1}
              max={360}
              step={1}
              suffix="°/s"
              onChange={(v) =>
                updateLayer<ImageLayer>(l.id, { rotateSpeed: v })
              }
            />
          )}

          <NumberRow
            label="Transparency"
            value={l.transparency}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) => updateLayer<ImageLayer>(l.id, { transparency: v })}
          />

          <Toggle
            label="Beat Zoom"
            checked={l.beatZoom}
            onChange={(v) => updateLayer<ImageLayer>(l.id, { beatZoom: v })}
          />
          {l.beatZoom && (
            <>
              <NumberRow
                label="Zoom amount"
                value={l.beatZoomAmount}
                min={0.02}
                max={0.6}
                step={0.01}
                onChange={(v) =>
                  updateLayer<ImageLayer>(l.id, { beatZoomAmount: v })
                }
              />
              <Label>Beat division</Label>
              <ButtonGroup
                value={String(l.beatDivision) as "1" | "2" | "4" | "8"}
                onChange={(v) =>
                  updateLayer<ImageLayer>(l.id, {
                    beatDivision: Number(v) as 1 | 2 | 4 | 8,
                  })
                }
                options={[
                  { value: "1", label: "1x" },
                  { value: "2", label: "2x" },
                  { value: "4", label: "4x" },
                  { value: "8", label: "8x" },
                ]}
              />
            </>
          )}

          <NumberRow
            label="Outline width"
            value={l.outlineWidth}
            min={0}
            max={40}
            step={1}
            onChange={(v) => updateLayer<ImageLayer>(l.id, { outlineWidth: v })}
          />
          {l.outlineWidth > 0 && (
            <>
              <Label>Outline color</Label>
              <ColorInput
                value={l.outlineColor}
                onChange={(v) =>
                  updateLayer<ImageLayer>(l.id, { outlineColor: v })
                }
              />
            </>
          )}

          <NumberRow
            label="Opacity"
            value={l.opacity}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) => updateLayer<ImageLayer>(l.id, { opacity: v })}
          />
          <NumberRow
            label="Rotation (static)"
            value={l.rotation}
            min={-180}
            max={180}
            step={1}
            suffix="°"
            onChange={(v) => updateLayer<ImageLayer>(l.id, { rotation: v })}
          />
        </PanelSection>
      ))}
    </>
  );
}
