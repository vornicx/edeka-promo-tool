"use client";

import { useEffect, useState } from "react";
import {
  AISettings,
  ProviderPayload,
  ProviderPublic,
  PROVIDER_PRESETS,
  getAISettings,
  saveAISettings,
} from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PROVIDER_NAMES: Record<string, string> = {
  openrouter: "OpenRouter",
  gemini: "Google Gemini",
  github: "GitHub Models",
  nvidia: "NVIDIA NIM",
  ollama: "Ollama",
  custom: "Benutzerdefiniert",
};

function uid(): string {
  return Math.random().toString(36).slice(2, 10);
}

function CloseIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

function ChevronUp() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  );
}

function ChevronDown() {
  return (
    <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

type UIConfig = ProviderPayload;

function emptyProvider(): UIConfig {
  return {
    id: uid(),
    type: "openrouter",
    base_url: PROVIDER_PRESETS.openrouter.base_url,
    model: PROVIDER_PRESETS.openrouter.model,
    enabled: true,
  };
}

function fromPublic(publics: ProviderPublic[]): UIConfig[] {
  return publics.map((p) => ({
    id: p.id,
    type: p.type,
    base_url: p.base_url,
    model: p.model,
    enabled: p.enabled,
  }));
}

export default function SettingsPanel({ open, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [providers, setProviders] = useState<UIConfig[]>([]);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    setLoading(true);
    getAISettings()
      .then((data) => {
        if (cancelled) return;
        setSettings(data);
        setProviders(fromPublic(data.providers));
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

  const updateProvider = (id: string, patch: Partial<UIConfig>) => {
    setProviders((prev) => prev.map((p) => (p.id === id ? { ...p, ...patch } : p)));
  };

  const handleTypeChange = (id: string, type: string) => {
    const preset = PROVIDER_PRESETS[type];
    if (preset) {
      updateProvider(id, { type, base_url: preset.base_url, model: preset.model });
    } else {
      updateProvider(id, { type });
    }
  };

  const moveProvider = (index: number, direction: "up" | "down") => {
    const target = index + (direction === "up" ? -1 : 1);
    if (target < 0 || target >= providers.length) return;
    setProviders((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  const removeProvider = (id: string) => {
    setProviders((prev) => prev.filter((p) => p.id !== id));
  };

  const addProvider = () => {
    setProviders((prev) => [...prev, emptyProvider()]);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!providers.length) {
      showToast("error", "Mindestens einen Anbieter konfigurieren oder das Panel schließen");
      return;
    }
    setSaving(true);
    try {
      const nextSettings = await saveAISettings({
        providers: providers.map((p) => ({
          ...p,
          api_key: p.api_key?.trim() ? p.api_key.trim() : undefined,
        })),
      });
      setSettings(nextSettings);
      setProviders(fromPublic(nextSettings.providers));
      showToast("success", "KI-Einstellungen gespeichert");
      onClose();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Einstellungen konnten nicht gespeichert werden");
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  const hasAnyKey = settings?.providers.some((p) => p.has_api_key) ?? false;

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
            <h2 className="mt-2 text-2xl font-extrabold text-slate-950">KI-Anbieter verwalten</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {hasAnyKey
                ? "Mehrere Anbieter als Fallback-Kette. Die Reihenfolge bestimmt die Priorität."
                : "Optional. Ohne Key funktioniert das Studio im Profi-Modus weiter."}
            </p>
          </div>
          <button type="button" className="icon-btn" aria-label="Einstellungen schließen" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="grid flex-1 content-start gap-4 overflow-y-auto p-5">
          {loading ? (
            <div className="grid min-h-40 place-items-center text-sm font-bold text-slate-500">
              <span className="flex items-center gap-2">
                <span className="spinner" />
                Einstellungen werden geladen
              </span>
            </div>
          ) : (
            <>
              {providers.map((provider, index) => {
                const preset = PROVIDER_PRESETS[provider.type];
                const publicInfo = settings?.providers.find((p) => p.id === provider.id);

                return (
                  <div
                    key={provider.id}
                    className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
                  >
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          title="Nach oben"
                          className="icon-btn h-7 w-7"
                          disabled={index === 0}
                          onClick={() => moveProvider(index, "up")}
                        >
                          <ChevronUp />
                        </button>
                        <button
                          type="button"
                          title="Nach unten"
                          className="icon-btn h-7 w-7"
                          disabled={index === providers.length - 1}
                          onClick={() => moveProvider(index, "down")}
                        >
                          <ChevronDown />
                        </button>
                        <span className="text-xs font-extrabold uppercase tracking-[0.12em] text-slate-400">
                          #{index + 1}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {provider.enabled && (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                            Aktiv
                          </span>
                        )}
                        <button
                          type="button"
                          className="icon-btn h-7 w-7 text-red-500 hover:bg-red-50 hover:text-red-700"
                          aria-label="Anbieter entfernen"
                          onClick={() => removeProvider(provider.id)}
                        >
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    </div>

                    <div className="grid gap-3">
                      <div>
                        <label className="label !mb-1">Anbieter</label>
                        <select
                          className="input !min-h-9"
                          value={provider.type}
                          onChange={(e) => handleTypeChange(provider.id, e.target.value)}
                        >
                          {Object.entries(PROVIDER_NAMES).map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="label !mb-1">API-Key</label>
                        <input
                          className="input !min-h-9"
                          type="password"
                          placeholder={
                            publicInfo?.has_api_key
                              ? "Leer lassen, um den Key zu behalten"
                              : `API-Key für ${PROVIDER_NAMES[provider.type] || provider.type}`
                          }
                          value={(provider.api_key as string) || ""}
                          onChange={(e) => updateProvider(provider.id, { api_key: e.target.value })}
                          autoComplete="off"
                        />
                        {publicInfo?.masked_api_key && (
                          <p className="mt-1 text-xs font-medium text-slate-400">
                            Gespeichert: {publicInfo.masked_api_key}
                          </p>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="label !mb-1">Basis-URL</label>
                          <input
                            className="input !min-h-9"
                            value={provider.base_url}
                            onChange={(e) => updateProvider(provider.id, { base_url: e.target.value })}
                            placeholder="https://..."
                          />
                        </div>
                        <div>
                          <label className="label !mb-1">Modell</label>
                          <input
                            className="input !min-h-9"
                            value={provider.model}
                            onChange={(e) => updateProvider(provider.id, { model: e.target.value })}
                            placeholder="Modellname"
                          />
                        </div>
                      </div>

                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-slate-300 text-edeka-blue focus:ring-edeka-blue/20"
                          checked={provider.enabled}
                          onChange={(e) => updateProvider(provider.id, { enabled: e.target.checked })}
                        />
                        <span className="text-xs font-semibold text-slate-700">Aktiviert</span>
                      </label>
                    </div>
                  </div>
                );
              })}

              <button
                type="button"
                className="btn-ghost justify-self-start sm:w-auto"
                onClick={addProvider}
              >
                + Anbieter hinzufügen
              </button>

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
