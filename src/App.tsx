import { LayersPanel } from "@/components/LayersPanel";
import { PreviewCanvas } from "@/components/PreviewCanvas";
import { RightSidebar } from "@/components/RightSidebar";

export default function App() {
  return (
    <div className="h-full w-full flex flex-col">
      <header className="h-12 shrink-0 flex items-center justify-between px-4 border-b border-[var(--color-border)] bg-[var(--color-bg-0)]">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-[var(--color-accent)] to-[var(--color-accent-2)] flex items-center justify-center text-white font-bold">
            ♫
          </div>
          <h1 className="text-sm font-semibold">
            Music Spectrum &amp; Lyrics Video Studio
          </h1>
          <span className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] px-2 py-0.5 rounded-full border border-[var(--color-border)]">
            Beat-Reactive
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-[var(--color-text-muted)]">
          <a
            href="https://groq.com"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            Powered by Groq AI for lyrics
          </a>
        </div>
      </header>
      <div className="flex-1 min-h-0 flex">
        <LayersPanel />
        <main className="flex-1 min-w-0 bg-[var(--color-bg-0)] relative">
          <PreviewCanvas />
        </main>
        <RightSidebar />
      </div>
    </div>
  );
}
