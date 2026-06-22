"use client";

import { useRef, useState } from "react";
import Confetti from "@/components/Confetti";
import DirectionPicker from "@/components/DirectionPicker";
import ExportPanel from "@/components/ExportPanel";
import PreviewPanel from "@/components/PreviewPanel";
import PromoForm from "@/components/PromoForm";
import ProductLibraryPanel from "@/components/ProductLibraryPanel";
import SettingsPanel from "@/components/SettingsPanel";
import ToastContainer, { showToast } from "@/components/Toast";
import { CreativeDirection, composePromo } from "@/lib/api";

const STEPS = [
  {
    label: "Briefing",
    description: "Produkt, Preis und Kontext",
    icon: "M8 7h8M8 11h8M8 15h5M6 3h12a2 2 0 012 2v14l-4-2-4 2-4-2-4 2V5a2 2 0 012-2z",
  },
  {
    label: "Richtung",
    description: "Kreativen Ansatz wählen",
    icon: "M12 3l2.6 5.3 5.9.9-4.2 4.1 1 5.8L12 16.4 6.7 19.1l1-5.8-4.2-4.1 5.9-.9L12 3z",
  },
  {
    label: "Gestaltung",
    description: "Finale Promotion erstellen",
    icon: "M4 7h16M4 12h10M4 17h16M18 10l3 3-3 3",
  },
  {
    label: "Export",
    description: "Formate herunterladen",
    icon: "M12 3v11m0 0l-4-4m4 4l4-4M5 19h14",
  },
];

function Icon({ d, className = "h-4 w-4" }: { d: string; className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d={d} />
    </svg>
  );
}

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [directions, setDirections] = useState<CreativeDirection[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [composed, setComposed] = useState(false);
  const [composeVersion, setComposeVersion] = useState(0);
  const [composing, setComposing] = useState(false);
  const [error, setError] = useState("");
  const [generationMode, setGenerationMode] = useState("");
  const [generationNote, setGenerationNote] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);
  const workspaceRef = useRef<HTMLDivElement>(null);

  const step = !sessionId ? 1 : selectedIndex === null ? 2 : !composed ? 3 : 4;
  const selectedDirection = selectedIndex !== null ? directions[selectedIndex] : null;

  const handleCreated = (sid: string, dirs: CreativeDirection[], mode: string, note: string) => {
    setSessionId(sid);
    setDirections(dirs);
    setSelectedIndex(null);
    setComposed(false);
    setGenerationMode(mode);
    setGenerationNote(note);
    setError("");
    showToast("success", mode === "ai" ? "Richtungen mit KI erstellt" : "Richtungen lokal erstellt");
    setTimeout(() => workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
  };

  const handleSelectDirection = (index: number) => {
    if (index !== selectedIndex) setComposed(false);
    setSelectedIndex(index);
    setError("");
  };

  const handleTryAnother = () => {
    setComposed(false);
    setError("");
    setTimeout(() => workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
  };

  const handleReset = () => {
    setSessionId(null);
    setDirections([]);
    setSelectedIndex(null);
    setComposed(false);
    setComposing(false);
    setError("");
    setGenerationMode("");
    setGenerationNote("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCompose = async () => {
    if (!sessionId || selectedIndex === null) return;
    setComposing(true);
    setError("");
    try {
      await composePromo(sessionId, selectedIndex);
      setComposed(true);
      setComposeVersion((v) => v + 1);
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 2500);
      showToast("success", "Promotion ist bereit");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Promotion konnte nicht gestaltet werden";
      setError(msg);
      showToast("error", msg);
    } finally {
      setComposing(false);
    }
  };

  return (
    <div className="min-h-screen bg-app">
      <Confetti active={showConfetti} />
      <ToastContainer />
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <ProductLibraryPanel open={productsOpen} onClose={() => setProductsOpen(false)} />

      <header className="border-b border-slate-200/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-edeka-blue shadow-brand">
              <span className="text-sm font-extrabold tracking-tight text-edeka-yellow">EM</span>
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-base font-extrabold text-slate-950">EDEKA Mühlenbein Promo Studio</h1>
              <p className="text-xs font-medium text-slate-500">Aktionen für Markt und Social Media erstellen</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {sessionId && (
              <button type="button" className="btn-ghost hidden w-auto md:inline-flex" onClick={handleReset}>
                Neue Aktion
              </button>
            )}
            <button type="button" className="btn-ghost hidden w-auto md:inline-flex" onClick={() => setProductsOpen(true)}>
              Produkte
            </button>
            <button type="button" className="icon-btn md:hidden" aria-label="Produkte verwalten" onClick={() => setProductsOpen(true)}>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 7l8-4 8 4-8 4-8-4zm0 0v10l8 4 8-4V7M12 11v10" />
              </svg>
            </button>
            <button type="button" className="btn-ghost hidden w-auto md:inline-flex" onClick={() => setSettingsOpen(true)}>
              KI-Einstellungen
            </button>
            <button type="button" className="icon-btn md:hidden" aria-label="KI-Einstellungen öffnen" onClick={() => setSettingsOpen(true)}>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M10.3 4.3l.6-1.3h2.2l.6 1.3 1.4.6 1.3-.5 1.6 1.6-.5 1.3.6 1.4 1.3.6v2.2l-1.3.6-.6 1.4.5 1.3-1.6 1.6-1.3-.5-1.4.6-.6 1.3h-2.2l-.6-1.3-1.4-.6-1.3.5L6 14.8l.5-1.3-.6-1.4-1.3-.6V9.3l1.3-.6.6-1.4L6 6l1.6-1.6 1.3.5 1.4-.6zM12 9a3 3 0 100 6 3 3 0 000-6z" />
              </svg>
            </button>
            <div className="hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 md:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-semibold text-slate-600">
                {sessionId ? `Aktive Sitzung · Schritt ${step}/4` : "Bereit zum Erstellen"}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main ref={workspaceRef} className="mx-auto grid max-w-7xl gap-6 px-5 py-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-8">
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <section className="panel p-5">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Workflow</p>
            <h2 className="mt-2 text-2xl font-extrabold leading-tight text-slate-950">Vom Angebot zur fertigen Promotion</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Briefing ausfüllen, kreative Richtungen vergleichen und im passenden Format exportieren.
            </p>
          </section>

          <nav className="panel p-3" aria-label="Erstellungsfortschritt">
            {STEPS.map((item, index) => {
              const position = index + 1;
              const active = step === position;
              const done = step > position;
              return (
                <div
                  key={item.label}
                  className={`flex items-start gap-3 rounded-lg p-3 transition-colors ${
                    active ? "bg-edeka-lightblue text-edeka-blue" : done ? "text-emerald-700" : "text-slate-400"
                  }`}
                >
                  <span
                    className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${
                      active
                        ? "border-edeka-blue/20 bg-white"
                        : done
                          ? "border-emerald-200 bg-emerald-50"
                          : "border-slate-200 bg-white"
                    }`}
                  >
                    <Icon d={item.icon} className="h-4 w-4" />
                  </span>
                  <span>
                    <span className="block text-sm font-bold text-slate-900">{item.label}</span>
                    <span className="block text-xs font-medium leading-5 text-slate-500">{item.description}</span>
                  </span>
                </div>
              );
            })}
          </nav>

          {selectedDirection && (
            <section className="panel p-4">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Gewählte Richtung</p>
              <h3 className="mt-2 text-sm font-extrabold capitalize text-slate-950">
                {selectedDirection.name.replace(/_/g, " ")}
              </h3>
              <div className="mt-3 flex gap-1.5">
                {selectedDirection.palette.slice(0, 5).map((color, index) => (
                  <span
                    key={`${color}-${index}`}
                    className="h-7 flex-1 rounded-md border border-white shadow-sm"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-600">{selectedDirection.intent}</p>
            </section>
          )}
        </aside>

        <div className="space-y-5">
          {step === 1 && (
            <section className="animate-slide-up">
              <PromoForm onCreated={handleCreated} />
            </section>
          )}

          {directions.length > 0 && step >= 2 && (
            <section className="animate-slide-up space-y-5">
              <DirectionPicker directions={directions} selectedIndex={selectedIndex} onSelect={handleSelectDirection} />

              {generationMode && (
                <div className="panel flex flex-col gap-2 p-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Erstellungsmodus</p>
                    <p className="mt-1 text-sm font-semibold text-slate-700">
                      {generationMode === "ai" ? "KI-optimierter Plan" : "Lokaler Profi-Modus"}
                    </p>
                  </div>
                  {generationNote && <p className="max-w-2xl text-sm leading-6 text-slate-500">{generationNote}</p>}
                </div>
              )}

              {selectedIndex !== null && !composed && (
                <div className="panel flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Nächster Schritt</p>
                    <h2 className="mt-1 text-xl font-extrabold text-slate-950">Promotion gestalten</h2>
                    <p className="mt-1 text-sm text-slate-600">
                      Die gewählte Richtung wird zur finalen Promotion ausgearbeitet.
                    </p>
                  </div>
                  <button onClick={handleCompose} disabled={composing} className="btn-primary md:w-auto">
                    {composing ? (
                      <span className="flex items-center gap-2">
                        <span className="spinner" />
                        Wird gestaltet
                      </span>
                    ) : (
                      "Promotion gestalten"
                    )}
                  </button>
                </div>
              )}

              {error && (
                <div className="animate-shake rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
                  {error}
                </div>
              )}
            </section>
          )}

          {composed && (
            <section className="animate-slide-up space-y-5">
              <div className="panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Fertig</p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">
                    Promotion erstellt. Du kannst eine andere Richtung testen oder neu starten.
                  </p>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <button type="button" className="btn-ghost sm:w-auto" onClick={handleTryAnother}>
                    Andere Richtung testen
                  </button>
                  <button type="button" className="btn-ghost sm:w-auto" onClick={handleReset}>
                    Neue Aktion
                  </button>
                </div>
              </div>

              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
                <PreviewPanel sessionId={sessionId} composed={composed} version={composeVersion} />
                <ExportPanel sessionId={sessionId} composed={composed} />
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
