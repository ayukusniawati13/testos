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
import type { TextLayer } from "@/types/studio";
import { Plus, Trash2 } from "lucide-react";

export function TextPanel() {
  const layers = useStudio((s) => s.layers);
  const selectedLayerId = useStudio((s) => s.selectedLayerId);
  const addTextLayer = useStudio((s) => s.addTextLayer);
  const removeLayer = useStudio((s) => s.removeLayer);
  const updateLayer = useStudio((s) => s.updateLayer);
  const setSelectedLayer = useStudio((s) => s.setSelectedLayer);

  const textLayers = layers.filter((l): l is TextLayer => l.type === "text");

  return (
    <>
      <PanelSection title="Text Elements">
        <button
          type="button"
          onClick={addTextLayer}
          className="inline-flex items-center justify-center gap-2 px-3 py-2 w-full rounded-md text-sm bg-[var(--color-accent)] hover:bg-[var(--color-accent-hi)] text-white"
        >
          <Plus size={14} /> Add Text
        </button>
        <div className="space-y-1.5 mt-2">
          {textLayers.map((l) => (
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
              <span
                className="truncate flex-1 text-left"
                style={{ fontFamily: l.fontFamily }}
              >
                {l.text || "(empty)"}
              </span>
              <IconBtn title="Remove" onClick={() => removeLayer(l.id)} danger>
                <Trash2 size={12} />
              </IconBtn>
            </button>
          ))}
          {textLayers.length === 0 && (
            <p className="text-[11px] text-[var(--color-text-muted)]">
              Add titles, captions, watermarks. Every text supports font, size,
              style, color, outline, shadow and beat zoom.
            </p>
          )}
        </div>
      </PanelSection>

      {textLayers.map((l) => (
        <PanelSection
          key={l.id}
          title={`${l.text.slice(0, 18) || "Text"} — Settings`}
          defaultOpen={l.id === selectedLayerId}
        >
          <Label>Text</Label>
          <TextInput
            value={l.text}
            onChange={(v) => updateLayer<TextLayer>(l.id, { text: v })}
          />
          <Label>Font</Label>
          <Select
            value={l.fontFamily}
            onChange={(v) => updateLayer<TextLayer>(l.id, { fontFamily: v })}
            options={FONT_OPTIONS.map((f) => ({
              value: f.family,
              label: f.label,
            }))}
          />
          <NumberRow
            label="Font size"
            value={l.fontSize}
            min={16}
            max={300}
            step={1}
            suffix="px"
            onChange={(v) => updateLayer<TextLayer>(l.id, { fontSize: v })}
          />
          <Label>Weight</Label>
          <ButtonGroup
            value={String(l.fontWeight) as "300" | "400" | "500" | "600" | "700" | "800"}
            onChange={(v) =>
              updateLayer<TextLayer>(l.id, {
                fontWeight: Number(v) as TextLayer["fontWeight"],
              })
            }
            options={[
              { value: "300", label: "Light" },
              { value: "400", label: "Reg" },
              { value: "600", label: "Med" },
              { value: "700", label: "Bold" },
              { value: "800", label: "X-Bold" },
            ]}
            size="sm"
          />
          <Toggle
            label="Italic"
            checked={l.italic}
            onChange={(v) => updateLayer<TextLayer>(l.id, { italic: v })}
          />
          <Label>Alignment</Label>
          <ButtonGroup
            value={l.align}
            onChange={(v) => updateLayer<TextLayer>(l.id, { align: v })}
            options={[
              { value: "left", label: "Left" },
              { value: "center", label: "Center" },
              { value: "right", label: "Right" },
            ]}
            size="sm"
          />
          <Label>Color</Label>
          <ColorInput
            value={l.color}
            onChange={(v) => updateLayer<TextLayer>(l.id, { color: v })}
          />
          <NumberRow
            label="Outline width"
            value={l.strokeWidth}
            min={0}
            max={30}
            step={1}
            onChange={(v) => updateLayer<TextLayer>(l.id, { strokeWidth: v })}
          />
          {l.strokeWidth > 0 && (
            <>
              <Label>Outline color</Label>
              <ColorInput
                value={l.strokeColor}
                onChange={(v) =>
                  updateLayer<TextLayer>(l.id, { strokeColor: v })
                }
              />
            </>
          )}
          <Toggle
            label="Drop shadow"
            checked={l.shadow}
            onChange={(v) => updateLayer<TextLayer>(l.id, { shadow: v })}
          />
          <Toggle
            label="Beat zoom"
            checked={l.beatZoom}
            onChange={(v) => updateLayer<TextLayer>(l.id, { beatZoom: v })}
          />
          {l.beatZoom && (
            <NumberRow
              label="Zoom amount"
              value={l.beatZoomAmount}
              min={0.02}
              max={0.6}
              step={0.01}
              onChange={(v) =>
                updateLayer<TextLayer>(l.id, { beatZoomAmount: v })
              }
            />
          )}
          <NumberRow
            label="Opacity"
            value={l.opacity}
            min={0}
            max={1}
            step={0.01}
            onChange={(v) => updateLayer<TextLayer>(l.id, { opacity: v })}
          />
          <NumberRow
            label="Rotation"
            value={l.rotation}
            min={-180}
            max={180}
            step={1}
            suffix="°"
            onChange={(v) => updateLayer<TextLayer>(l.id, { rotation: v })}
          />
        </PanelSection>
      ))}
    </>
  );
}
