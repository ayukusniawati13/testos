export interface FontOption {
  family: string;
  label: string;
  category: "sans" | "serif" | "display" | "handwriting" | "mono";
}

export const FONT_OPTIONS: FontOption[] = [
  { family: "Inter", label: "Inter", category: "sans" },
  { family: "Poppins", label: "Poppins", category: "sans" },
  { family: "Montserrat", label: "Montserrat", category: "sans" },
  { family: "Roboto", label: "Roboto", category: "sans" },
  { family: "Raleway", label: "Raleway", category: "sans" },
  { family: "Nunito", label: "Nunito", category: "sans" },
  { family: "Quicksand", label: "Quicksand", category: "sans" },
  { family: "Source Sans 3", label: "Source Sans", category: "sans" },
  { family: "Fredoka", label: "Fredoka", category: "sans" },
  { family: "Comfortaa", label: "Comfortaa", category: "sans" },
  { family: "Oswald", label: "Oswald", category: "display" },
  { family: "Bebas Neue", label: "Bebas Neue", category: "display" },
  { family: "Anton", label: "Anton", category: "display" },
  { family: "Russo One", label: "Russo One", category: "display" },
  { family: "Audiowide", label: "Audiowide", category: "display" },
  { family: "Righteous", label: "Righteous", category: "display" },
  { family: "Orbitron", label: "Orbitron", category: "display" },
  { family: "Press Start 2P", label: "Press Start 2P", category: "display" },
  { family: "Permanent Marker", label: "Permanent Marker", category: "display" },
  { family: "Playfair Display", label: "Playfair Display", category: "serif" },
  { family: "Lora", label: "Lora", category: "serif" },
  { family: "Pacifico", label: "Pacifico", category: "handwriting" },
  { family: "Lobster", label: "Lobster", category: "handwriting" },
  { family: "Caveat", label: "Caveat", category: "handwriting" },
  { family: "Dancing Script", label: "Dancing Script", category: "handwriting" },
  { family: "JetBrains Mono", label: "JetBrains Mono", category: "mono" },
];

export function getFontStack(family: string): string {
  return `"${family}", ui-sans-serif, system-ui, sans-serif`;
}
