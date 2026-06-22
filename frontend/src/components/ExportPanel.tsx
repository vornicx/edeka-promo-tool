"use client";

import { useState } from "react";
import { exportPromo } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

const FORMATS = [
  { value: "post", label: "Post 1:1", dim: "1080 x 1080", use: "Feed" },
  { value: "story", label: "Story 9:16", dim: "1080 x 1920", use: "Instagram" },
  { value: "poster_a4", label: "Plakat A4", dim: "2480 x 3508", use: "Druck" },
  { value: "poster_a5", label: "Plakat A5", dim: "1748 x 2480", use: "Markt" },
];

function DownloadIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M12 3v11m0 0l-4-4m4 4l4-4M5 19h14" />
    </svg>
  );
}

export default function ExportPanel({ sessionId, composed }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  if (!sessionId || !composed) return null;

  const handleExport = async (format: string) => {
    setBusy(format);
    setError("");
    try {
      const blob = await exportPromo(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `edeka_${format}.png`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Export konnte nicht erstellt werden");
    } finally {
      setBusy(null);
    }
  };

  return (
    <aside className="panel overflow-hidden xl:sticky xl:top-6 xl:self-start">
      <div className="border-b border-slate-200 bg-white p-5">
        <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Export</p>
        <h2 className="mt-2 text-xl font-extrabold text-slate-950">Formate herunterladen</h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">Wähle das passende Ausgabeformat für den Kanal.</p>
      </div>

      <div className="grid gap-3 p-5">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700">
            {error}
          </div>
        )}

        {FORMATS.map((format) => (
          <button
            key={format.value}
            type="button"
            onClick={() => handleExport(format.value)}
            disabled={busy !== null}
            className={`group flex items-center justify-between gap-3 rounded-lg border p-4 text-left transition-all ${
              busy === format.value
                ? "border-edeka-blue bg-edeka-lightblue"
                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-card"
            } disabled:cursor-not-allowed disabled:opacity-55`}
          >
            <span>
              <span className="block text-sm font-extrabold text-slate-950">{format.label}</span>
              <span className="mt-1 block text-xs font-semibold text-slate-500">{format.use} · {format.dim}</span>
            </span>
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-600 transition-colors group-hover:bg-edeka-blue group-hover:text-white">
              {busy === format.value ? <span className="spinner" /> : <DownloadIcon />}
            </span>
          </button>
        ))}
      </div>
    </aside>
  );
}
