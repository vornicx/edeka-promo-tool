"use client";

import { useRef, useState } from "react";
import Confetti from "@/components/Confetti";
import ExportPanel from "@/components/ExportPanel";
import HistoryPanel from "@/components/HistoryPanel";
import PreviewPanel from "@/components/PreviewPanel";
import PromoForm from "@/components/PromoForm";
import ProductLibraryPanel from "@/components/ProductLibraryPanel";
import SettingsPanel from "@/components/SettingsPanel";
import ToastContainer, { showToast } from "@/components/Toast";
import {
  CreativeDirection,
  PromoVariant,
  PromotionData,
  composeAllPromo,
  getVariantImageUrl,
  selectVariant,
} from "@/lib/api";
import { makeThumbnail, saveHistoryEntry } from "@/lib/history";

const STEPS = [
  {
    label: "Briefing",
    description: "Produkt und Preis",
    icon: "M8 7h8M8 11h8M8 15h5M6 3h12a2 2 0 012 2v14l-4-2-4 2-4-2-4 2V5a2 2 0 012-2z",
  },
  {
    label: "Gestaltung",
    description: "Motiv entsteht",
    icon: "M4 7h16M4 12h10M4 17h16M18 10l3 3-3 3",
  },
  {
    label: "Export",
    description: "Bild speichern",
    icon: "M12 3v11m0 0l-4-4m4 4l4-4M5 19h14",
  },
];

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [composed, setComposed] = useState(false);
  const [composeVersion, setComposeVersion] = useState(0);
  const [composing, setComposing] = useState(false);
  const [exportFormat, setExportFormat] = useState("post");
  const [productName, setProductName] = useState("");
  const [error, setError] = useState("");
  const [generationMode, setGenerationMode] = useState("");
  const [generationNote, setGenerationNote] = useState("");
  const [showConfetti, setShowConfetti] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [variants, setVariants] = useState<PromoVariant[]>([]);
  const [selectedVariant, setSelectedVariant] = useState(0);
  const [switchingVariant, setSwitchingVariant] = useState(false);
  // Das Formular bleibt gemountet (nur versteckt), damit „Anpassen" alle
  // Eingaben behält. Ein neuer key setzt es bei „Neue Aktion" zurück.
  const [formKey, setFormKey] = useState(0);
  const [prefill, setPrefill] = useState<{ data: Partial<PromotionData>; nonce: number } | null>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);

  const step = !sessionId ? 1 : !composed ? 2 : 3;

  // Direct flow: after the briefing we compose all design variants immediately
  // and let the user pick one visually — no separate parameter page.
  const handleCreated = async (sid: string, _dirs: CreativeDirection[], mode: string, note: string, form: PromotionData) => {
    setSessionId(sid);
    setComposed(false);
    setGenerationMode(mode);
    setGenerationNote(note);
    setExportFormat(form.format);
    setProductName(form.product);
    setError("");
    setComposing(true);
    setVariants([]);
    setSelectedVariant(0);
    setTimeout(() => workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    try {
      const res = await composeAllPromo(sid);
      setVariants(res.variants);
      setSelectedVariant(res.selected);
      setComposed(true);
      setComposeVersion((v) => v + 1);
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 2500);
      showToast("success", "Promotion ist bereit");
      // Aktion in die lokale Historie schreiben (best effort).
      try {
        const thumb = await makeThumbnail(`${getVariantImageUrl(sid, res.selected)}?v=${Date.now()}`);
        saveHistoryEntry(form, thumb);
      } catch {
        /* Historie ist optional — Fehler hier nie dem Nutzer zeigen */
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Promotion konnte nicht gestaltet werden";
      setError(msg);
      showToast("error", msg);
    } finally {
      setComposing(false);
    }
  };

  const handlePickVariant = async (index: number) => {
    if (!sessionId || index === selectedVariant || switchingVariant) return;
    setSwitchingVariant(true);
    try {
      await selectVariant(sessionId, index);
      setSelectedVariant(index);
      setComposeVersion((v) => v + 1);
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Variante konnte nicht gewählt werden");
    } finally {
      setSwitchingVariant(false);
    }
  };

  const backToBriefing = () => {
    setSessionId(null);
    setComposed(false);
    setComposing(false);
    setError("");
    setGenerationMode("");
    setGenerationNote("");
    setVariants([]);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // „Anpassen": zurück zum Briefing mit allen Eingaben.
  const handleEdit = () => backToBriefing();

  // „Neue Aktion": Briefing leeren (Formular wird neu gemountet).
  const handleReset = () => {
    setFormKey((k) => k + 1);
    setPrefill(null);
    backToBriefing();
  };

  const handleReuse = (data: PromotionData) => {
    setPrefill({ data, nonce: Date.now() });
    backToBriefing();
    showToast("success", "Aktion ins Briefing übernommen");
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <div className="min-h-screen bg-app">
      <Confetti active={showConfetti} />
      <ToastContainer />
      <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <ProductLibraryPanel open={productsOpen} onClose={() => setProductsOpen(false)} />
      <HistoryPanel open={historyOpen} onClose={() => setHistoryOpen(false)} onReuse={handleReuse} />

      <header className="header-brand text-white shadow-brand">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white shadow-sm">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/waschbaer_logo.png" alt="EDEKA Waschbär" className="h-10 w-10 object-contain" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-base font-extrabold leading-tight text-white sm:text-lg">EDEKA Mühlenbein</h1>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-yellow">Promo Studio</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {sessionId && (
              <button type="button" className="btn-header hidden md:inline-flex" onClick={handleReset}>
                Neue Aktion
              </button>
            )}
            <button type="button" className="btn-header hidden md:inline-flex" onClick={() => setHistoryOpen(true)}>
              Meine Aktionen
            </button>
            <button type="button" className="icon-btn-header md:hidden" aria-label="Meine Aktionen öffnen" onClick={() => setHistoryOpen(true)}>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button type="button" className="btn-header hidden md:inline-flex" onClick={() => setProductsOpen(true)}>
              Eigene Produkte
            </button>
            <button type="button" className="icon-btn-header md:hidden" aria-label="Produkte verwalten" onClick={() => setProductsOpen(true)}>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 7l8-4 8 4-8 4-8-4zm0 0v10l8 4 8-4V7M12 11v10" />
              </svg>
            </button>
            <button type="button" className="btn-header hidden md:inline-flex" onClick={() => setSettingsOpen(true)}>
              KI
            </button>
            <button type="button" className="icon-btn-header md:hidden" aria-label="KI-Einstellungen öffnen" onClick={() => setSettingsOpen(true)}>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M10.3 4.3l.6-1.3h2.2l.6 1.3 1.4.6 1.3-.5 1.6 1.6-.5 1.3.6 1.4 1.3.6v2.2l-1.3.6-.6 1.4.5 1.3-1.6 1.6-1.3-.5-1.4.6-.6 1.3h-2.2l-.6-1.3-1.4-.6-1.3.5L6 14.8l.5-1.3-.6-1.4-1.3-.6V9.3l1.3-.6.6-1.4L6 6l1.6-1.6 1.3.5 1.4-.6zM12 9a3 3 0 100 6 3 3 0 000-6z" />
              </svg>
            </button>
            <div className="hidden items-center gap-2 rounded-pill bg-white/10 px-3 py-2 ring-1 ring-inset ring-white/15 lg:flex">
              <span className="h-2 w-2 rounded-full bg-edeka-yellow" />
              <span className="text-xs font-semibold text-white/90">
                {sessionId ? `Schritt ${step}/${STEPS.length}` : "Bereit"}
              </span>
            </div>
            <button type="button" className="btn-header hidden md:inline-flex" onClick={handleLogout}>
              Abmelden
            </button>
            <button type="button" className="icon-btn-header md:hidden" aria-label="Abmelden" onClick={handleLogout}>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 7l5 5-5 5M20 12H9m1-8H6a2 2 0 00-2 2v12a2 2 0 002 2h4" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main ref={workspaceRef} className="mx-auto grid max-w-7xl gap-6 px-5 py-6 lg:grid-cols-[320px_minmax(0,1fr)] lg:px-8">
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <section className="panel overflow-hidden">
            <div className="header-brand p-5 text-white">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-yellow">Workflow</p>
              <h2 className="mt-2 text-xl font-extrabold leading-tight text-white">In 3 Schritten zum Motiv</h2>
            </div>
            <p className="p-5 text-sm leading-6 text-slate-600">
              Füllen Sie die Angaben der Reihe nach aus. Pflicht sind nur Produkt, Preis und Zeitraum.
            </p>
          </section>

          <nav className="panel p-2.5" aria-label="Erstellungsfortschritt">
            {STEPS.map((item, index) => {
              const position = index + 1;
              const active = step === position;
              const done = step > position;
              return (
                <div
                  key={item.label}
                  className={`flex items-center gap-3 rounded-xl p-2.5 transition-colors ${
                    active ? "bg-edeka-lightblue" : ""
                  }`}
                >
                  <span
                    className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-extrabold transition-colors ${
                      active
                        ? "bg-edeka-blue text-white shadow-brand"
                        : done
                          ? "bg-edeka-yellow text-edeka-blue"
                          : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {done ? (
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      position
                    )}
                  </span>
                  <span>
                    <span className={`block text-sm font-bold ${active ? "text-edeka-blue" : "text-slate-900"}`}>{item.label}</span>
                    <span className="block text-xs font-medium leading-5 text-slate-500">{item.description}</span>
                  </span>
                </div>
              );
            })}
          </nav>

          {generationMode && (
            <section className="panel p-4">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">Modus</p>
              <p className="mt-2 text-sm font-bold text-slate-900">
                {generationMode === "ai" ? "KI-optimiert" : "Lokaler Profi-Modus"}
              </p>
              {generationNote && <p className="mt-2 text-xs leading-5 text-slate-500">{generationNote}</p>}
            </section>
          )}
        </aside>

        <div className="space-y-5">
          {step === 1 && (
            <section className="panel p-5 animate-slide-up">
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Neue Aktion</p>
              <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Was soll beworben werden?</h2>
              <p className="mt-2 max-w-3xl text-sm font-medium leading-6 text-slate-600">
                Starten Sie mit Produkt, Preis und Aktionszeitraum. Design und Format können Sie darunter auswählen; die Voreinstellungen passen bereits für eine schnelle Promotion.
              </p>
            </section>
          )}

          <section className={step === 1 ? "animate-slide-up" : "hidden"}>
            <PromoForm key={formKey} onCreated={handleCreated} prefill={prefill} />
          </section>

          {sessionId && !composed && composing && (
            <section className="panel flex items-center gap-3 p-6 animate-slide-up">
              <span className="spinner" />
              <p className="text-sm font-semibold text-slate-700">Promotion wird gestaltet …</p>
            </section>
          )}

          {error && !composed && (
            <div className="animate-shake rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
              {error}
            </div>
          )}

          {composed && (
            <section className="animate-slide-up space-y-5">
              {variants.length > 1 && sessionId && (
                <div className="panel p-5">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Designvarianten</p>
                  <p className="mt-1 text-sm font-medium text-slate-600">
                    Wählen Sie mit einem Klick das Design, das Ihnen am besten gefällt.
                  </p>
                  <div className="mt-3 grid grid-cols-3 gap-3">
                    {variants.map((variant) => {
                      const active = variant.index === selectedVariant;
                      return (
                        <button
                          key={variant.index}
                          type="button"
                          aria-pressed={active}
                          disabled={switchingVariant}
                          onClick={() => handlePickVariant(variant.index)}
                          className={`group overflow-hidden rounded-xl border text-left transition-all ${
                            active
                              ? "border-edeka-blue ring-2 ring-edeka-blue/25 shadow-brand"
                              : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-edeka-blue/40 hover:shadow-card"
                          }`}
                        >
                          <div className="relative aspect-square w-full bg-slate-100">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={`${getVariantImageUrl(sessionId, variant.index)}?v=${composeVersion}`}
                              alt={variant.label}
                              loading="lazy"
                              className="h-full w-full object-contain"
                            />
                            {active && (
                              <span className="absolute right-2 top-2 grid h-6 w-6 place-items-center rounded-full bg-edeka-blue text-white shadow-brand ring-2 ring-white">
                                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                              </span>
                            )}
                          </div>
                          <div className={`px-2.5 py-2 ${active ? "bg-edeka-lightblue" : "bg-white"}`}>
                            <p className={`text-xs font-bold ${active ? "text-edeka-blue" : "text-slate-900"}`}>{variant.label}</p>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <PreviewPanel sessionId={sessionId} composed={composed} version={composeVersion + selectedVariant * 1000} />

              <div className="panel flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Fertig</p>
                  <p className="mt-1 text-sm font-semibold text-slate-700">
                    Ihre Promotion ist bereit zum Herunterladen.
                  </p>
                </div>
                <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                  <button type="button" className="btn-ghost sm:w-auto" onClick={handleEdit}>
                    Anpassen
                  </button>
                  <button type="button" className="btn-ghost sm:w-auto" onClick={handleReset}>
                    Neue Aktion
                  </button>
                  <ExportPanel sessionId={sessionId} format={exportFormat} productName={productName} />
                </div>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
