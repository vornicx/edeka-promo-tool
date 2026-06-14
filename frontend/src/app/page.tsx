"use client";

import { useState } from "react";
import PromoForm from "@/components/PromoForm";
import DirectionPicker from "@/components/DirectionPicker";
import PreviewPanel from "@/components/PreviewPanel";
import ExportPanel from "@/components/ExportPanel";
import { CreativeDirection, composePromo } from "@/lib/api";

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [directions, setDirections] = useState<CreativeDirection[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [composed, setComposed] = useState(false);
  const [composing, setComposing] = useState(false);
  const [error, setError] = useState("");

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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-edeka-blue text-white py-4 shadow-lg">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl font-bold">EDEKA Mühlenbein</h1>
          <p className="text-blue-200">Promo Tool — Creación de promociones con IA</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        <PromoForm onCreated={handleCreated} />

        {directions.length > 0 && (
          <>
            <DirectionPicker
              directions={directions}
              selectedIndex={selectedIndex}
              onSelect={setSelectedIndex}
            />

            {selectedIndex !== null && (
              <div className="flex justify-center">
                <button
                  onClick={handleCompose}
                  disabled={composing}
                  className="btn-primary text-lg px-8"
                >
                  {composing ? "Componiendo..." : "Componer Promoción"}
                </button>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                {error}
              </div>
            )}

            <PreviewPanel sessionId={sessionId} composed={composed} />
            <ExportPanel sessionId={sessionId} composed={composed} />
          </>
        )}
      </main>
    </div>
  );
}
