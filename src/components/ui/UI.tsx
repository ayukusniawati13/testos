import { useState, type ChangeEvent, type ReactNode } from "react";

export function PanelSection({
  title,
  children,
  defaultOpen = true,
  right,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  right?: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-[var(--color-border)]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-xs uppercase tracking-wider text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
      >
        <span className="flex items-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full transition-colors ${
              open ? "bg-[var(--color-accent)]" : "bg-[var(--color-border-hi)]"
            }`}
          />
          {title}
        </span>
        <span className="flex items-center gap-2">
          {right}
          <span className="text-[var(--color-text-muted)]">{open ? "−" : "+"}</span>
        </span>
      </button>
      {open && <div className="px-4 pb-4 pt-1 space-y-3">{children}</div>}
    </div>
  );
}

export function Label({ children }: { children: ReactNode }) {
  return (
    <div className="text-[11px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">
      {children}
    </div>
  );
}

export function NumberRow({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  suffix,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
  suffix?: string;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11px] uppercase tracking-wider text-[var(--color-text-muted)]">
          {label}
        </span>
        <span className="text-xs text-[var(--color-text)] tabular-nums">
          {value.toFixed(step < 1 ? 2 : 0)}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

export function TextInput({
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: "text" | "password";
}) {
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 rounded-md text-sm bg-[var(--color-bg-3)] border border-[var(--color-border)] focus:border-[var(--color-accent)] outline-none"
    />
  );
}

export function Select<T extends string>({
  value,
  onChange,
  options,
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className="w-full px-3 py-2 rounded-md text-sm bg-[var(--color-bg-3)] border border-[var(--color-border)] focus:border-[var(--color-accent)] outline-none"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export function ColorInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-9 h-9 rounded-md bg-transparent border border-[var(--color-border)] cursor-pointer"
      />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="flex-1 px-3 py-2 rounded-md text-sm bg-[var(--color-bg-3)] border border-[var(--color-border)] focus:border-[var(--color-accent)] outline-none font-mono"
      />
    </div>
  );
}

export function ButtonGroup<T extends string>({
  value,
  onChange,
  options,
  size = "md",
}: {
  value: T;
  onChange: (v: T) => void;
  options: { value: T; label: string; icon?: ReactNode }[];
  size?: "sm" | "md";
}) {
  return (
    <div className="inline-flex w-full rounded-md bg-[var(--color-bg-3)] p-1 border border-[var(--color-border)]">
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            className={`flex-1 ${size === "sm" ? "px-2 py-1 text-xs" : "px-2.5 py-1.5 text-sm"} rounded transition-colors ${
              active
                ? "bg-[var(--color-accent)] text-white"
                : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
            }`}
          >
            {o.icon}
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <label className="flex items-center justify-between cursor-pointer select-none">
      <span className="text-xs text-[var(--color-text)]">{label}</span>
      <span
        onClick={() => onChange(!checked)}
        className={`relative inline-flex w-9 h-5 rounded-full transition-colors ${
          checked ? "bg-[var(--color-accent)]" : "bg-[var(--color-bg-3)]"
        } border border-[var(--color-border)]`}
      >
        <span
          className={`absolute top-0.5 ${
            checked ? "left-4" : "left-0.5"
          } w-4 h-4 rounded-full bg-white transition-all`}
        />
      </span>
    </label>
  );
}

export function FileButton({
  accept,
  multiple,
  onPick,
  children,
  variant = "primary",
}: {
  accept: string;
  multiple?: boolean;
  onPick: (files: File[]) => void;
  children: ReactNode;
  variant?: "primary" | "ghost";
}) {
  return (
    <label
      className={`inline-flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm cursor-pointer border ${
        variant === "primary"
          ? "bg-[var(--color-accent)] hover:bg-[var(--color-accent-hi)] border-[var(--color-accent-hi)] text-white"
          : "bg-[var(--color-bg-3)] hover:bg-[var(--color-bg-2)] border-[var(--color-border)] text-[var(--color-text)]"
      }`}
    >
      {children}
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={(e: ChangeEvent<HTMLInputElement>) => {
          const files = Array.from(e.target.files ?? []);
          if (files.length) onPick(files);
          e.target.value = "";
        }}
        className="hidden"
      />
    </label>
  );
}

export function IconBtn({
  onClick,
  title,
  active,
  children,
  danger,
}: {
  onClick: () => void;
  title: string;
  active?: boolean;
  children: ReactNode;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`p-1.5 rounded-md transition-colors ${
        active
          ? "bg-[var(--color-accent)] text-white"
          : "text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-3)]"
      } ${danger ? "hover:!text-[var(--color-danger)]" : ""}`}
    >
      {children}
    </button>
  );
}
