"use client";

import { useState } from "react";
import { exportPromo } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

const FORMATS = [
  { value: "post", label: "Instagram Post (1080x1080)" },
  { value: "story", label: "Instagram Story (1080x1920)" },
  { value: "poster_a4", label: "Poster A4" },
  { value: "poster_a5", label: "Poster A5" },
];

export default function ExportPanel({ sessionId, composed }: Props) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");

  if (!sessionId || !composed) return null;

  const handleExport = async (format: string) => {
    setExporting(true);
    setError("");
    try {
      const blob = await exportPromo(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `edeka_promo_${format}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al exportar";
      setError(msg);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-edeka-blue mb-4">Exportar</h2>
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {FORMATS.map((fmt) => (
          <button
            key={fmt.value}
            onClick={() => handleExport(fmt.value)}
            disabled={exporting}
            className="btn-secondary text-sm"
          >
            {exporting ? "Exportando..." : fmt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
