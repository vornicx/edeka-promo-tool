"use client";

import { useEffect, useState } from "react";
import { PromotionData } from "@/lib/api";
import { HistoryEntry, deleteHistoryEntry, listHistory } from "@/lib/history";

interface Props {
  open: boolean;
  onClose: () => void;
  onReuse: (data: PromotionData) => void;
}

const FORMAT_LABELS: Record<string, string> = {
  post: "Post 1:1",
  story: "Story 9:16",
  poster_a4: "Plakat A4",
  poster_a5: "Plakat A5",
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return "";
  }
}

export default function HistoryPanel({ open, onClose, onReuse }: Props) {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    if (open) setEntries(listHistory());
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/35 p-3 backdrop-blur-sm" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-xl animate-slide-up flex-col overflow-hidden rounded-lg border-t-4 border-edeka-yellow bg-white shadow-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Historie</p>
            <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Meine Aktionen</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Frühere Promotions mit einem Klick wiederverwenden — alle Angaben werden ins Briefing übernommen.
            </p>
          </div>
          <button type="button" className="icon-btn" aria-label="Schließen" onClick={onClose}>
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {entries.length === 0 ? (
            <p className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
              Noch keine Aktionen. Sobald Sie eine Promotion erstellen, erscheint sie hier automatisch.
            </p>
          ) : (
            <ul className="grid gap-3 sm:grid-cols-2">
              {entries.map((entry) => (
                <li key={entry.id} className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                  <div className="relative aspect-square bg-slate-100">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={entry.thumb} alt={entry.product} className="h-full w-full object-contain" />
                    <span className="absolute left-2 top-2 rounded-pill bg-slate-950/70 px-2 py-1 text-[10px] font-bold text-white backdrop-blur">
                      {FORMAT_LABELS[entry.format] ?? entry.format}
                    </span>
                  </div>
                  <div className="grid gap-2 p-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-bold text-slate-900">{entry.product}</p>
                      <p className="text-xs font-medium text-slate-500">{formatDate(entry.created)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className="flex-1 rounded-lg bg-edeka-blue px-3 py-2 text-xs font-extrabold text-white transition-opacity hover:opacity-90"
                        onClick={() => {
                          onReuse(entry.data);
                          onClose();
                        }}
                      >
                        Wiederverwenden
                      </button>
                      <button
                        type="button"
                        className="icon-btn"
                        aria-label={`${entry.product} löschen`}
                        onClick={() => setEntries(deleteHistoryEntry(entry.id))}
                      >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M6 7h12M9 7V5h6v2m-7 0v12a1 1 0 001 1h6a1 1 0 001-1V7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex justify-end border-t border-slate-200 bg-slate-50 p-5">
          <button type="button" className="btn-primary w-auto" onClick={onClose}>
            Fertig
          </button>
        </div>
      </div>
    </div>
  );
}
