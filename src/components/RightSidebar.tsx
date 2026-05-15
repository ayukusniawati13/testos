import { useStudio } from "@/store/studioStore";
import type { MenuId } from "@/types/studio";
import {
  AudioLines,
  Download,
  Image as ImageIcon,
  ImagePlay,
  Sparkles,
  Type,
  Wand2,
  Activity,
} from "lucide-react";
import type { ComponentType } from "react";
import { AudioPanel } from "./panels/AudioPanel";
import { ImagePanel } from "./panels/ImagePanel";
import { VisualizerPanel } from "./panels/VisualizerPanel";
import { BackgroundPanel } from "./panels/BackgroundPanel";
import { EffectsPanel } from "./panels/EffectsPanel";
import { TextPanel } from "./panels/TextPanel";
import { LyricsPanel } from "./panels/LyricsPanel";
import { ExportPanel } from "./panels/ExportPanel";

interface MenuItem {
  id: MenuId;
  label: string;
  Icon: ComponentType<{ size?: number; className?: string }>;
}

const MENU: MenuItem[] = [
  { id: "audio", label: "Audio", Icon: AudioLines },
  { id: "image", label: "Image", Icon: ImageIcon },
  { id: "visualizer", label: "Visualizer", Icon: Activity },
  { id: "background", label: "Background", Icon: ImagePlay },
  { id: "effects", label: "Effects", Icon: Wand2 },
  { id: "text", label: "Text", Icon: Type },
  { id: "lyrics", label: "Lyrics", Icon: Sparkles },
  { id: "export", label: "Export", Icon: Download },
];

const PANELS: Record<MenuId, ComponentType> = {
  audio: AudioPanel,
  image: ImagePanel,
  visualizer: VisualizerPanel,
  background: BackgroundPanel,
  effects: EffectsPanel,
  text: TextPanel,
  lyrics: LyricsPanel,
  export: ExportPanel,
};

export function RightSidebar() {
  const activeMenu = useStudio((s) => s.activeMenu);
  const setActiveMenu = useStudio((s) => s.setActiveMenu);

  return (
    <div className="flex">
      {activeMenu && (
        <aside className="w-80 shrink-0 bg-[var(--color-bg-1)] border-l border-[var(--color-border)] overflow-y-auto">
          <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between sticky top-0 bg-[var(--color-bg-1)] z-10">
            <span className="text-sm font-semibold capitalize">
              {MENU.find((m) => m.id === activeMenu)?.label} Menu
            </span>
          </div>
          {(() => {
            const Comp = PANELS[activeMenu];
            return <Comp />;
          })()}
        </aside>
      )}
      <nav className="w-16 shrink-0 bg-[var(--color-bg-0)] border-l border-[var(--color-border)] flex flex-col items-center py-3 gap-1">
        {MENU.map(({ id, label, Icon }) => {
          const active = activeMenu === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => setActiveMenu(id)}
              title={label}
              className={`relative w-12 h-12 rounded-xl flex flex-col items-center justify-center gap-0.5 transition-colors ${
                active
                  ? "bg-[var(--color-accent)] text-white"
                  : "text-[var(--color-text-muted)] hover:text-white hover:bg-[var(--color-bg-2)]"
              }`}
            >
              <Icon size={20} />
              <span className="text-[9px] uppercase tracking-wide">
                {label}
              </span>
              {active && (
                <span className="absolute -left-1 top-1/2 -translate-y-1/2 w-1 h-6 rounded-full bg-[var(--color-accent)]" />
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
