"use client";

import { useState } from "react";
import { exportPromo } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

const FORMATS = [
  { value: "post", label: "Post 1:1", dim: "1080×1080" },
  { value: "story", label: "Story 9:16", dim: "1080×1920" },
  { value: "poster_a4", label: "A4", dim: "2480×3508" },
  { value: "poster_a5", label: "A5", dim: "1748×2480" },
];

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
      setError("Error al exportar");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="card">
      <h2 className="section-title mb-4">Exportar</h2>
      {error && (
        <div className="mb-3 bg-red-50/80 border border-red-100 rounded-xl p-3 text-sm text-red-600">
          {error}
        </div>
      )}
      <div className="flex gap-2">
        {FORMATS.map((f) => (
          <button key={f.value} onClick={() => handleExport(f.value)}
            disabled={busy !== null}
            className={`flex-1 p-3 rounded-xl border text-center transition-all ${
              busy === f.value
                ? "border-edeka-blue/30 bg-edeka-lightblue/50"
                : "border-gray-100 bg-gray-50/50 hover:border-gray-200 hover:bg-white"
            } disabled:opacity-40`}>
            <div className="flex items-center justify-center gap-2 mb-0.5">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-sm font-semibold text-gray-700">{f.label}</span>
            </div>
            <div className="text-[11px] text-gray-400">{f.dim}</div>
            {busy === f.value && (
              <svg className="animate-spin h-3 w-3 mx-auto mt-1 text-edeka-blue" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
