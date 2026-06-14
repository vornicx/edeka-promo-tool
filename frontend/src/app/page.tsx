"use client";

import { useState } from "react";
import PromoForm from "@/components/PromoForm";
import DirectionPicker from "@/components/DirectionPicker";
import PreviewPanel from "@/components/PreviewPanel";
import ExportPanel from "@/components/ExportPanel";
import { CreativeDirection, composePromo } from "@/lib/api";

const STEPS = [
  { id: 1, label: "Datos" },
  { id: 2, label: "Dirección" },
  { id: 3, label: "Previsualizar" },
  { id: 4, label: "Exportar" },
];

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [directions, setDirections] = useState<CreativeDirection[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [composed, setComposed] = useState(false);
  const [composing, setComposing] = useState(false);
  const [error, setError] = useState("");

  const currentStep = !sessionId ? 1 : !selectedIndex ? 2 : !composed ? 3 : 4;

  const handleCreated = (sid: string, dirs: CreativeDirection[]) => {
    setSessionId(sid);
    setDirections(dirs);
    setSelectedIndex(null);
    setComposed(false);
    setError("");
  };

  const handleCompose = async () => {
    if (!sessionId || selectedIndex === null) return;
    setComposing(true);
    setError("");
    try {
      await composePromo(sessionId, selectedIndex);
      setComposed(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al componer");
    } finally {
      setComposing(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="bg-gradient-to-r from-edeka-blue via-edeka-darkblue to-edeka-blue text-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-edeka-yellow flex items-center justify-center flex-shrink-0 shadow-md">
              <span className="text-edeka-blue text-xl font-extrabold">EM</span>
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
                EDEKA Mühlenbein
              </h1>
              <p className="text-edeka-yellow/90 text-sm md:text-base font-medium">
                Promo Tool — Creador de promociones con IA
              </p>
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
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                      currentStep === step.id
                        ? "bg-edeka-blue text-white shadow-md scale-110"
                        : currentStep > step.id
                          ? "bg-green-500 text-white"
                          : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {currentStep > step.id ? "✓" : step.id}
                  </div>
                  <span
                    className={`text-xs mt-1 font-medium hidden md:block transition-colors ${
                      currentStep === step.id
                        ? "text-edeka-blue"
                        : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 rounded transition-colors duration-300 ${
                      currentStep > step.id ? "bg-green-400" : "bg-gray-200"
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10 space-y-6 md:space-y-8">
        <div className="animate-fade-in">
          <PromoForm onCreated={handleCreated} />
        </div>

        {directions.length > 0 && (
          <div className="animate-slide-up space-y-6">
            <DirectionPicker
              directions={directions}
              selectedIndex={selectedIndex}
              onSelect={setSelectedIndex}
            />

            {selectedIndex !== null && !composed && (
              <div className="flex justify-center animate-fade-in">
                <button
                  onClick={handleCompose}
                  disabled={composing}
                  className="btn-primary text-lg px-12 py-4 flex items-center gap-3"
                >
                  {composing ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      Componiendo...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                      Componer Promoción
                    </>
                  )}
                </button>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4 text-red-700 text-sm font-medium animate-fade-in flex items-center gap-3">
                <svg
                  className="w-5 h-5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                {error}
              </div>
            )}

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
