"use client";

import { PromotionData } from "@/lib/api";

// Lokale Aktionshistorie: Briefing + kleines Vorschaubild im localStorage.
// So kann der Nutzer jede frühere Aktion mit einem Klick wiederverwenden —
// unabhängig davon, ob der Server die Sitzung noch kennt.

export interface HistoryEntry {
  id: string;
  created: string; // ISO date
  product: string;
  format: string;
  thumb: string; // small JPEG data-URL
  data: PromotionData;
}

const STORAGE_KEY = "edeka_promo_history_v1";
const MAX_ENTRIES = 24;
const THUMB_MAX = 420;

function read(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(entries: HistoryEntry[]): void {
  // Bei vollem Speicher älteste Einträge opfern statt zu scheitern.
  for (let keep = entries.length; keep > 0; keep = Math.floor(keep / 2)) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries.slice(0, keep)));
      return;
    } catch {
      /* quota exceeded — try with fewer entries */
    }
  }
}

export function listHistory(): HistoryEntry[] {
  return read();
}

export function deleteHistoryEntry(id: string): HistoryEntry[] {
  const entries = read().filter((e) => e.id !== id);
  write(entries);
  return entries;
}

export async function makeThumbnail(imageUrl: string): Promise<string> {
  const res = await fetch(imageUrl);
  if (!res.ok) throw new Error("Vorschau konnte nicht geladen werden");
  const bitmap = await createImageBitmap(await res.blob());
  const scale = Math.min(1, THUMB_MAX / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas nicht verfügbar");
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas.toDataURL("image/jpeg", 0.82);
}

export function saveHistoryEntry(data: PromotionData, thumb: string): HistoryEntry {
  const entry: HistoryEntry = {
    id: `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`,
    created: new Date().toISOString(),
    product: data.product,
    format: data.format,
    thumb,
    data,
  };
  write([entry, ...read()].slice(0, MAX_ENTRIES));
  return entry;
}
