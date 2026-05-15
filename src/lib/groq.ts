import type { LyricLine } from "@/types/studio";

/**
 * Calls Groq's Whisper-large-v3 endpoint to transcribe audio with word-level
 * timestamps, then groups words into lyric lines.
 */
export async function transcribeWithGroq(
  apiKey: string,
  audioFile: File,
  opts: { language?: string; model?: string } = {},
): Promise<LyricLine[]> {
  const form = new FormData();
  form.append("file", audioFile);
  form.append("model", opts.model ?? "whisper-large-v3");
  form.append("response_format", "verbose_json");
  form.append("timestamp_granularities[]", "segment");
  form.append("timestamp_granularities[]", "word");
  if (opts.language) form.append("language", opts.language);

  const res = await fetch(
    "https://api.groq.com/openai/v1/audio/transcriptions",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: form,
    },
  );
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Groq transcription failed (${res.status}): ${text || res.statusText}`,
    );
  }
  const data = (await res.json()) as {
    segments?: { start: number; end: number; text: string }[];
    text?: string;
  };
  if (data.segments && data.segments.length > 0) {
    return data.segments.map((s) => ({
      time: s.start,
      duration: Math.max(0.1, s.end - s.start),
      text: s.text.trim(),
    }));
  }
  // Fallback: single line at start
  if (data.text) {
    return [{ time: 0, duration: 5, text: data.text.trim() }];
  }
  return [];
}
