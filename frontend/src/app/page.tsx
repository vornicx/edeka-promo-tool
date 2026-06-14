"use client";

import { useState, useEffect, useRef } from "react";
import PromoForm from "@/components/PromoForm";
import DirectionPicker from "@/components/DirectionPicker";
import PreviewPanel from "@/components/PreviewPanel";
import ExportPanel from "@/components/ExportPanel";
import Confetti from "@/components/Confetti";
import ToastContainer, { showToast } from "@/components/Toast";
import { CreativeDirection, composePromo } from "@/lib/api";

const STEPS = [
  { id: 1, label: "Datos", icon: "document" },
  { id: 2, label: "Dirección", icon: "bulb" },
  { id: 3, label: "Previsualizar", icon: "image" },
  { id: 4, label: "Exportar", icon: "download" },
];

function StepIcon({ icon, className }: { icon: string; className: string }) {
  const paths: Record<string, string> = {
    document: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
    bulb: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
    image: "M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z",
    download: "M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  };
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={paths[icon]} />
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

  const currentStep = !sessionId ? 1 : selectedIndex === null ? 2 : !composed ? 3 : 4;

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [currentStep]);

  const handleCreated = (sid: string, dirs: CreativeDirection[]) => {
    setSessionId(sid);
    setDirections(dirs);
    setSelectedIndex(null);
    setComposed(false);
    setError("");
    showToast("success", "Promoción creada", `${dirs.length} direcciones creativas generadas`);
    setTimeout(() => {
      document.getElementById("step-directions")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
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
      showToast("success", "Promoción compuesta", "El diseño se ha generado correctamente");
      setTimeout(() => {
        document.getElementById("step-preview")?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al componer";
      setError(msg);
      showToast("error", "Error al componer", msg);
    } finally {
      setComposing(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Confetti active={showConfetti} />
      <ToastContainer />

      <header className="bg-gradient-to-r from-edeka-blue via-edeka-darkblue to-edeka-blue text-white shadow-lg relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(255,214,0,0.1),transparent_50%)]" />
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-5 relative">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-edeka-yellow flex items-center justify-center flex-shrink-0 shadow-md ring-2 ring-edeka-yellow/50">
              <span className="text-edeka-blue text-xl font-extrabold">EM</span>
            </div>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
                EDEKA Mühlenbein
              </h1>
              <p className="text-edeka-yellow/90 text-sm md:text-base font-medium">
                Promo Tool — Creador de promociones con IA
              </p>
            </div>
            <div className="hidden md:flex items-center gap-2 bg-white/10 rounded-xl px-4 py-2 backdrop-blur-sm">
              <span className="text-xs font-medium text-edeka-yellow/80">Paso</span>
              <span className="text-lg font-extrabold text-white">{currentStep}</span>
              <span className="text-xs text-white/60">/ 4</span>
            </div>
          </div>
        </div>
      </header>

      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-3">
          <div className="flex items-center justify-between max-w-xl mx-auto">
            {STEPS.map((step, i) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-500 ${
                      currentStep === step.id
                        ? "bg-edeka-blue text-white shadow-md scale-110 ring-2 ring-edeka-blue/30"
                        : currentStep > step.id
                          ? "bg-green-500 text-white"
                          : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {currentStep > step.id ? (
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <StepIcon icon={step.icon} className="w-4 h-4" />
                    )}
                  </div>
                  <span
                    className={`text-xs mt-1.5 font-semibold hidden md:block transition-colors duration-300 ${
                      currentStep >= step.id ? "text-edeka-blue" : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 rounded transition-all duration-500 ${
                      currentStep > step.id ? "bg-green-400" : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </nav>

      <main ref={mainRef} className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10 space-y-6 md:space-y-8">
        <div className={`transition-all duration-500 ${currentStep === 1 ? "animate-fade-in" : "opacity-60"}`}>
          <PromoForm onCreated={handleCreated} />
        </div>

        {directions.length > 0 && (
          <div
            id="step-directions"
            className={`transition-all duration-500 ${
              currentStep === 2 ? "animate-slide-up" : currentStep > 2 ? "opacity-60 scale-[0.99]" : ""
            }`}
          >
            <DirectionPicker
              directions={directions}
              selectedIndex={selectedIndex}
              onSelect={setSelectedIndex}
            />

            {selectedIndex !== null && !composed && (
              <div className="flex justify-center mt-6 animate-fade-in">
                <button
                  onClick={handleCompose}
                  disabled={composing}
                  className="btn-primary text-lg px-12 py-4 flex items-center gap-3 shadow-elevated"
                >
                  {composing ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      <span>Componiendo...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span>Componer Promoción</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {error && (
              <div className="animate-shake mt-4 bg-red-50 border-2 border-red-200 rounded-xl p-4 text-red-700 text-sm font-medium flex items-center gap-3">
                <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}
          </div>
        )}

        {composed && (
          <div
            id="step-preview"
            className={`space-y-6 stagger-children ${composed ? "animate-fade-in" : ""}`}
          >
            <PreviewPanel sessionId={sessionId} composed={composed} />
            <ExportPanel sessionId={sessionId} composed={composed} />
          </div>
        )}
      </main>

      <footer className="border-t border-gray-200 bg-white/50 backdrop-blur-sm mt-12">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-4 text-center text-sm text-gray-500">
          EDEKA Mühlenbein Promo Tool &copy; {new Date().getFullYear()}
        </div>
      </footer>
    </div>
  );
}
