"use client";

import { useState, useRef } from "react";
import PromoForm from "@/components/PromoForm";
import DirectionPicker from "@/components/DirectionPicker";
import PreviewPanel from "@/components/PreviewPanel";
import ExportPanel from "@/components/ExportPanel";
import Confetti from "@/components/Confetti";
import ToastContainer, { showToast } from "@/components/Toast";
import { CreativeDirection, composePromo } from "@/lib/api";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [directions, setDirections] = useState<CreativeDirection[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [composed, setComposed] = useState(false);
  const [composing, setComposing] = useState(false);
  const [error, setError] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const step = !sessionId ? 1 : selectedIndex === null ? 2 : !composed ? 3 : 4;

  const handleCreated = (sid: string, dirs: CreativeDirection[]) => {
    setSessionId(sid);
    setDirections(dirs);
    setSelectedIndex(null);
    setComposed(false);
    setError("");
    showToast("success", "Direcciones generadas");
    contentRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleCompose = async () => {
    if (!sessionId || selectedIndex === null) return;
    setComposing(true);
    setError("");
    try {
      await composePromo(sessionId, selectedIndex);
      setComposed(true);
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 3500);
      showToast("success", "Promoción compuesta");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error";
      setError(msg);
      showToast("error", msg);
    } finally {
      setComposing(false);
    }
  };

  const STEPS = ["Datos", "Dirección", "Preview", "Exportar"];
  const stepIcons = ["📋", "🎨", "👁", "⬇"];

  return (
    <div className="min-h-screen">
      <Confetti active={showConfetti} />
      <ToastContainer />

      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-edeka-blue flex items-center justify-center">
                <span className="text-edeka-yellow text-sm font-extrabold">EM</span>
              </div>
              <div>
                <h1 className="text-base font-extrabold text-gray-900">EDEKA Mühlenbein</h1>
                <p className="text-[11px] text-gray-500 font-medium -mt-0.5">Promo Tool</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {STEPS.map((s, i) => (
                <div key={s} className="flex items-center">
                  <div
                    className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs font-semibold transition-all ${
                      step === i + 1
                        ? "bg-edeka-blue/10 text-edeka-blue"
                        : step > i + 1
                          ? "text-green-600"
                          : "text-gray-400"
                    }`}
                  >
                    <span className="text-[10px]">{stepIcons[i]}</span>
                    <span className="hidden sm:inline">{s}</span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div className={`w-4 h-[1.5px] mx-1 ${step > i + 1 ? "bg-green-300" : "bg-gray-200"}`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main ref={contentRef} className="max-w-4xl mx-auto px-4 py-5">
        <div className={`${step === 1 ? "animate-fade-in" : "hidden"}`}>
          <PromoForm onCreated={handleCreated} />
        </div>

        {directions.length > 0 && (
          <div className={`${step === 2 || step === 3 || step === 4 ? "animate-fade-in" : "hidden"}`}>
            <DirectionPicker
              directions={directions}
              selectedIndex={selectedIndex}
              onSelect={setSelectedIndex}
            />

            {selectedIndex !== null && !composed && (
              <div className="flex justify-center mt-4">
                <button
                  onClick={handleCompose}
                  disabled={composing}
                  className="btn-primary flex items-center gap-2 text-sm"
                >
                  {composing ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Componiendo...
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      Componer Promoción
                    </>
                  )}
                </button>
              </div>
            )}

            {error && (
              <div className="animate-shake mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm flex items-center gap-2">
                <span>⚠</span>
                {error}
              </div>
            )}
          </div>
        )}

        {composed && (
          <div className="mt-4 space-y-4 stagger-children">
            <PreviewPanel sessionId={sessionId} composed={composed} />
            <ExportPanel sessionId={sessionId} composed={composed} />
          </div>
        )}
      </main>
    </div>
  );
}
