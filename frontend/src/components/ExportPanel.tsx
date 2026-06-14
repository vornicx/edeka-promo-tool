"use client";

import { useState } from "react";
import { exportPromo } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

const FORMATS = [
  { value: "post", label: "Instagram Post", icon: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z", detail: "1080x1080" },
  { value: "story", label: "Instagram Story", icon: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z", detail: "1080x1920" },
  { value: "poster_a4", label: "Póster A4", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", detail: "2480x3508" },
  { value: "poster_a5", label: "Póster A5", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z", detail: "1748x2480" },
];

export default function ExportPanel({ sessionId, composed }: Props) {
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState<string | null>(null);

  if (!sessionId || !composed) return null;

  const handleExport = async (format: string) => {
    setExporting(format);
    setError("");
    setSuccess(null);
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
      setSuccess(format);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al exportar";
      setError(msg);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="glass-card-strong animate-slide-up">
      <div className="flex items-center gap-3 pb-2 border-b border-white/40 mb-5">
        <div className="w-10 h-10 rounded-xl bg-edeka-yellow/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-edeka-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-extrabold text-edeka-blue">Exportar</h2>
          <p className="text-sm text-gray-500">Descarga la promoción en el formato que necesites</p>
        </div>
      </div>

      {error && (
        <div className="glass-strong border-red-300/40 rounded-xl p-4 mb-4 text-red-700 text-sm font-medium flex items-center gap-3 animate-fade-in">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {FORMATS.map((fmt) => (
          <button
            key={fmt.value}
            onClick={() => handleExport(fmt.value)}
            disabled={exporting !== null}
              className={`relative p-4 rounded-2xl border-2 text-left transition-all duration-200 ${
                success === fmt.value
                  ? "border-green-400/50 bg-green-50/60 backdrop-blur-sm"
                  : "border-white/40 bg-white/30 backdrop-blur-sm hover:bg-white/50 hover:border-edeka-yellow/50"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {success === fmt.value && (
              <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center shadow animate-bounce-in">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}
            <div className="flex items-center gap-2 mb-2">
              <svg className={`w-5 h-5 ${success === fmt.value ? "text-green-600" : "text-edeka-blue"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={fmt.icon} />
              </svg>
              <span className="text-sm font-bold">{fmt.label}</span>
            </div>
            <div className="text-xs text-gray-500">{fmt.detail}</div>
            {exporting === fmt.value && (
              <div className="absolute inset-0 rounded-2xl bg-white/60 flex items-center justify-center">
                <svg className="animate-spin h-6 w-6 text-edeka-blue" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
