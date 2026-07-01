import { useCallback, useEffect, useState } from "react";

// A saved design preset: a reusable combination of the look controls
// (style + tone + level + accent colour + price size). Persisted locally.
export interface DesignPreset {
  id: string;
  name: string;
  style: string;
  tone: string;
  differentiation_level: string;
  accent_color: string;
  price_size: string;
}

const KEY = "edeka_design_presets_v1";

// Starter presets that showcase the look controls; users can edit/delete them.
const DEFAULT_PRESETS: DesignPreset[] = [
  { id: "seed-knaller", name: "EDEKA Knaller", style: "edeka", tone: "atrevido", differentiation_level: "alto", accent_color: "", price_size: "xl" },
  { id: "seed-premium", name: "Premium Gold", style: "luxe", tone: "premium", differentiation_level: "medio", accent_color: "#CEA74E", price_size: "l" },
  { id: "seed-frisch", name: "Frische Grün", style: "frischemarkt", tone: "fresco", differentiation_level: "medio", accent_color: "", price_size: "m" },
  { id: "seed-bio", name: "Bio Natur", style: "bio", tone: "local", differentiation_level: "medio", accent_color: "", price_size: "m" },
  { id: "seed-tafel", name: "Markt-Tafel", style: "markttafel", tone: "premium", differentiation_level: "medio", accent_color: "", price_size: "l" },
];

function loadPresets(): DesignPreset[] {
  if (typeof window === "undefined") return DEFAULT_PRESETS;
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return DEFAULT_PRESETS;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as DesignPreset[]) : DEFAULT_PRESETS;
  } catch {
    return DEFAULT_PRESETS;
  }
}

function save(next: DesignPreset[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    // Ignore quota / privacy-mode failures — presets are a convenience only.
  }
}

export function useDesignPresets() {
  const [presets, setPresets] = useState<DesignPreset[]>(DEFAULT_PRESETS);

  // Hydrate from localStorage after mount (initial render matches SSR default).
  useEffect(() => {
    setPresets(loadPresets());
  }, []);

  const addPreset = useCallback((p: Omit<DesignPreset, "id">) => {
    setPresets((prev) => {
      const next = [...prev, { ...p, id: `p-${Date.now().toString(36)}` }];
      save(next);
      return next;
    });
  }, []);

  const removePreset = useCallback((id: string) => {
    setPresets((prev) => {
      const next = prev.filter((x) => x.id !== id);
      save(next);
      return next;
    });
  }, []);

  return { presets, addPreset, removePreset };
}
