"use client";

import { useState } from "react";
import { exportPromo } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

const FORMATS = [
  { value: "post", label: "📱 Post 1:1", detail: "1080×1080" },
  { value: "story", label: "📱 Story 9:16", detail: "1080×1920" },
  { value: "poster_a4", label: "📄 A4", detail: "2480×3508" },
  { value: "poster_a5", label: "📄 A5", detail: "1748×2480" },
];

export default function ExportPanel({ sessionId, composed }: Props) {
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState("");

  if (!sessionId || !composed) return null;

  const handleExport = async (format: string) => {
    setExporting(format);
    setError("");
    try {
      const blob = await exportPromo(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `edeka_${format}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setError("Error al exportar");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">⬇</span>
        <h2 className="text-sm font-bold text-gray-700">Exportar</h2>
      </div>

      {error && (
        <div className="mb-2 bg-red-50 border border-red-200 rounded-lg p-2 text-xs text-red-600 flex items-center gap-1.5">
          <span>⚠</span>
          {error}
        </div>
      )}

      <div className="flex gap-2">
        {FORMATS.map((f) => (
          <button
            key={f.value}
            onClick={() => handleExport(f.value)}
            disabled={exporting !== null}
            className={`flex-1 p-3 rounded-lg border text-center transition-all ${
              exporting === f.value
                ? "border-edeka-blue bg-edeka-lightblue/50"
                : "border-gray-100 bg-gray-50/50 hover:border-gray-200 hover:bg-white"
            } disabled:opacity-40`}
          >
            <div className="text-sm font-semibold text-gray-700">{f.label}</div>
            <div className="text-[10px] text-gray-400 mt-0.5">{f.detail}</div>
            {exporting === f.value && (
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
