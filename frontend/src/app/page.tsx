"use client";

import { useState, useRef } from "react";
import PromoForm from "@/components/PromoForm";
import DirectionPicker from "@/components/DirectionPicker";
import PreviewPanel from "@/components/PreviewPanel";
import ExportPanel from "@/components/ExportPanel";
import Confetti from "@/components/Confetti";
import ToastContainer, { showToast } from "@/components/Toast";
import { CreativeDirection, composePromo } from "@/lib/api";

const STEPS = [
  { label: "Datos", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
  { label: "Dirección", icon: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" },
  { label: "Vista previa", icon: "M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" },
  { label: "Exportar", icon: "M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
];

function StepIcon({ d, className }: { d: string; className?: string }) {
  return (
    <svg className={className || "w-3.5 h-3.5"} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={d} />
    </svg>
  );
}

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [directions, setDirections] = useState<CreativeDirection[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [composed, setComposed] = useState(false);
  const [composing, setComposing] = useState(false);
  const [error, setError] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  const step = !sessionId ? 1 : selectedIndex === null ? 2 : !composed ? 3 : 4;

  const handleCreated = (sid: string, dirs: CreativeDirection[]) => {
    setSessionId(sid);
    setDirections(dirs);
    setSelectedIndex(null);
    setComposed(false);
    setError("");
    showToast("success", "Direcciones generadas");
    setTimeout(() => mainRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  };

  const handleCompose = async () => {
    if (!sessionId || selectedIndex === null) return;
    setComposing(true);
    setError("");
    try {
      await composePromo(sessionId, selectedIndex);
      setComposed(true);
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 2500);
      showToast("success", "Promoción lista");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error";
      setError(msg);
      showToast("error", msg);
    } finally {
      setComposing(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Confetti active={showConfetti} />
      <ToastContainer />

      <header className="bg-white border-b border-gray-100">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-edeka-blue flex items-center justify-center">
                <span className="text-edeka-yellow text-xs font-extrabold">EM</span>
              </div>
              <div>
                <h1 className="text-sm font-bold text-gray-900">EDEKA Mühlenbein</h1>
                <p className="text-[11px] text-gray-400 font-medium -mt-0.5">Promo Tool</p>
              </div>
            </div>

            <div className="flex items-center gap-0.5">
              {STEPS.map((s, i) => {
                const active = step === i + 1;
                const done = step > i + 1;
                return (
                  <div key={s.label} className="flex items-center">
                    <div
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg transition-all text-xs font-semibold ${
                        active
                          ? "bg-edeka-blue/8 text-edeka-blue"
                          : done
                            ? "text-green-600"
                            : "text-gray-300"
                      }`}
                    >
                      <StepIcon d={s.icon} className={`w-3.5 h-3.5 ${done ? "text-green-500" : ""}`} />
                      <span className="hidden sm:inline">{s.label}</span>
                    </div>
                    {i < STEPS.length - 1 && (
                      <div className={`w-3 h-px mx-0.5 ${done ? "bg-green-300" : "bg-gray-200"}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </header>

      <main ref={mainRef} className="max-w-2xl mx-auto px-4 py-6">
        {step === 1 && (
          <div className="animate-fade-in">
            <PromoForm onCreated={handleCreated} />
          </div>
        )}

        {directions.length > 0 && step >= 2 && (
          <div className="animate-fade-in">
            <DirectionPicker
              directions={directions}
              selectedIndex={selectedIndex}
              onSelect={setSelectedIndex}
            />

            {selectedIndex !== null && !composed && (
              <div className="flex justify-center mt-4 animate-fade-in">
                <button onClick={handleCompose} disabled={composing} className="btn-primary">
                  {composing ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Componiendo
                    </span>
                  ) : (
                    "Componer promoción"
                  )}
                </button>
              </div>
            )}

            {error && (
              <div className="animate-shake mt-3 bg-red-50/80 border border-red-100 rounded-xl p-3 text-red-600 text-sm">
                {error}
              </div>
            )}
          </div>
        )}

        {composed && (
          <div className="mt-4 space-y-4">
            <PreviewPanel sessionId={sessionId} composed={composed} />
            <ExportPanel sessionId={sessionId} composed={composed} />
          </div>
        )}
      </main>
    </div>
  );
}
