"use client";

import { useEffect, useState } from "react";
import {
  AIModelInfo,
  getAISettings,
  getAIModels,
  saveAISettings,
} from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface SettingsData {
  api_key: string;
  selected_model: string;
  image_model: string;
  enabled: boolean;
  has_api_key: boolean;
  masked_api_key: string;
  settings_path: string;
}

const IMAGE_MODELS = [
  {
    id: "google/gemini-3.1-flash-image",
    name: "Nano Banana 2",
    meta: "Beste Standardwahl",
  },
  {
    id: "google/gemini-2.5-flash-image",
    name: "Nano Banana",
    meta: "Schnell und günstig",
  },
  {
    id: "openai/gpt-image-1-mini",
    name: "GPT Image Mini",
    meta: "Fallback für reale Bilder",
  },
];

function CloseIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

export default function SettingsPanel({ open, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [models, setModels] = useState<AIModelInfo[]>([]);
  const [apiKey, setApiKey] = useState("");
  const [selectedModel, setSelectedModel] = useState("google/gemini-2.5-flash-lite");
  const [imageModel, setImageModel] = useState("google/gemini-3.1-flash-image");
  const [filter, setFilter] = useState<"all" | "free" | "vision">("all");

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    setLoading(true);

    Promise.all([
      getAISettings(),
      getAIModels(),
    ])
      .then(([settingsData, modelsData]) => {
        if (cancelled) return;
        setSettings(settingsData);
        setModels(modelsData);
        setSelectedModel(settingsData.selected_model || "google/gemini-2.5-flash-lite");
        setImageModel(settingsData.image_model || "google/gemini-3.1-flash-image");
        setApiKey("");
      })
      .catch((err: unknown) => {
        showToast("error", err instanceof Error ? err.message : "Einstellungen konnten nicht geladen werden");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const nextSettings = await saveAISettings({
        api_key: apiKey.trim() || undefined,
        selected_model: selectedModel,
        image_model: imageModel,
        enabled: true,
      });
      setSettings(nextSettings);
      setApiKey("");
      showToast("success", "KI-Einstellungen gespeichert");
      onClose();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Einstellungen konnten nicht gespeichert werden");
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  const filteredModels = models.filter((m) => {
    if (filter === "free") return m.free;
    if (filter === "vision") return m.vision;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/35 p-3 backdrop-blur-sm" onClick={onClose}>
      <form
        onSubmit={handleSave}
        className="flex h-full w-full max-w-lg animate-slide-up flex-col overflow-hidden rounded-lg border-t-4 border-edeka-yellow bg-white shadow-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">KI</p>
            <h2 className="mt-2 text-2xl font-extrabold text-slate-950">KI-Design aktivieren</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {settings?.has_api_key
                ? `Aktiver Key: ${settings.masked_api_key}`
                : "OpenRouter API-Key eintragen. Ohne Key arbeitet das Studio im Profi-Modus."}
            </p>
          </div>
          <button type="button" className="icon-btn" aria-label="Einstellungen schließen" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="border-b border-slate-200 bg-edeka-lightblue/60 p-3 text-xs leading-5 text-edeka-blue">
          <strong>Empfehlung:</strong> Gemini 2.5 Flash Lite kostet nur Bruchteile eines Cents pro Entwurf und liefert stabilere Designrichtungen als Gratis-Modelle.{" "}
          <a
            href="https://openrouter.ai/google/gemini-2.5-flash-lite"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-edeka-darkblue"
          >
            Preise ansehen
          </a>{" "}
          · API-Key auf{" "}
          <a
            href="https://openrouter.ai/keys"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-2 hover:text-edeka-darkblue"
          >
            openrouter.ai/keys
          </a>{" "}
          erstellen.
        </div>

        <div className="grid flex-1 content-start gap-4 overflow-y-auto p-5">
          {loading ? (
            <div className="grid min-h-40 place-items-center text-sm font-bold text-slate-500">
              <span className="flex items-center gap-2">
                <span className="spinner" />
                Modelle werden geladen
              </span>
            </div>
          ) : (
            <>
              <div>
                <label className="label" htmlFor="api-key">OpenRouter API-Key</label>
                <input
                  id="api-key"
                  className="input"
                  type="password"
                  placeholder={
                    settings?.has_api_key
                      ? "Leer lassen, um den aktuellen Key zu behalten"
                      : "sk-or-v1-..."
                  }
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  autoComplete="off"
                />
                {settings?.masked_api_key && (
                  <p className="mt-1 text-xs font-medium text-slate-400">
                    Gespeichert: {settings.masked_api_key}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between gap-3">
                  <label className="label mb-0">Planungsmodell</label>
                  <div className="segmented w-auto">
                    {[
                      { value: "all", label: "Alle" },
                      { value: "free", label: "Gratis" },
                      { value: "vision", label: "Vision" },
                    ].map((f) => (
                      <button
                        key={f.value}
                        type="button"
                        className={`segment !px-3 ${filter === f.value ? "segment-active" : ""}`}
                        onClick={() => setFilter(f.value as "all" | "free" | "vision")}
                      >
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-3 grid gap-2">
                  {filteredModels.map((model) => {
                    const active = selectedModel === model.id;
                    return (
                      <button
                        key={model.id}
                        type="button"
                        onClick={() => setSelectedModel(model.id)}
                        className={`flex items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                          active
                            ? "border-edeka-blue ring-2 ring-edeka-blue/25 bg-edeka-lightblue/60"
                            : "border-slate-200 bg-white hover:border-edeka-blue/30"
                        }`}
                      >
                        <div className={`mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 ${
                          active ? "border-edeka-blue bg-edeka-blue" : "border-slate-300"
                        }`}>
                          {active && (
                            <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-extrabold text-slate-900">{model.name}</p>
                            <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-500">{model.provider}</span>
                            {model.free && (
                              <span className="rounded-md bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700">GRATIS</span>
                            )}
                            {model.vision && (
                              <span className="rounded-md bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Vision</span>
                            )}
                          </div>
                          <p className="mt-0.5 text-xs leading-5 text-slate-500">{model.description}</p>
                          <div className="mt-1 flex items-center gap-3 text-[10px] font-bold text-slate-400">
                            <span>Qualität: {model.quality}/100</span>
                            <span>Kontext: {model.context}</span>
                            <span className="text-edeka-blue">pro Design: {model.cost_est_design}</span>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-lg border border-edeka-blue/15 bg-edeka-lightblue/60 p-4">
                <label className="label">Bildmodell für KI-Events</label>
                <p className="mb-3 text-xs leading-5 text-slate-600">
                  Dieses Modell erzeugt das reale Bildmotiv für Event-Plakate. Ohne erfolgreiches Bild wird kein einfaches Ersatzlayout erstellt.
                </p>
                <div className="grid gap-2">
                  {IMAGE_MODELS.map((model) => {
                    const active = imageModel === model.id;
                    return (
                      <button
                        key={model.id}
                        type="button"
                        onClick={() => setImageModel(model.id)}
                        className={`rounded-lg border p-3 text-left transition-all ${
                          active
                            ? "border-edeka-blue bg-white text-edeka-blue ring-2 ring-edeka-blue/20"
                            : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/35"
                        }`}
                      >
                        <span className="block text-sm font-extrabold">{model.name}</span>
                        <span className="mt-0.5 block text-xs font-semibold text-slate-500">{model.id}</span>
                        <span className="mt-1 block text-xs leading-5 text-slate-500">{model.meta}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {settings?.settings_path && (
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Lokal gespeichert</p>
                  <p className="mt-1 break-all text-xs font-semibold leading-5 text-slate-600">{settings.settings_path}</p>
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex flex-col gap-3 border-t border-slate-200 bg-slate-50 p-5 sm:flex-row sm:justify-end">
          <button type="button" className="btn-ghost sm:w-auto" onClick={onClose}>
            Abbrechen
          </button>
          <button type="submit" className="btn-primary sm:w-auto" disabled={saving || loading}>
            {saving ? (
              <span className="flex items-center gap-2">
                <span className="spinner" />
                Speichern
              </span>
            ) : (
              "Einstellungen speichern"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
