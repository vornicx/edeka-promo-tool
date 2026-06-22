"use client";

import { useEffect, useState } from "react";
import { AISettings, getAISettings, saveAISettings } from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PROVIDERS = [
  {
    value: "openrouter",
    label: "OpenRouter",
    baseUrl: "https://openrouter.ai/api/v1",
    model: "openai/gpt-4o-mini",
  },
  {
    value: "custom",
    label: "OpenAI-kompatibel",
    baseUrl: "https://api.openai.com/v1",
    model: "gpt-4o-mini",
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
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [provider, setProvider] = useState("openrouter");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState(PROVIDERS[0].baseUrl);
  const [model, setModel] = useState(PROVIDERS[0].model);

  useEffect(() => {
    if (!open) return;

    let cancelled = false;
    setLoading(true);
    getAISettings()
      .then((data) => {
        if (cancelled) return;
        setSettings(data);
        setProvider(data.provider);
        setBaseUrl(data.base_url);
        setModel(data.model);
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

  const handleProviderChange = (nextProvider: string) => {
    setProvider(nextProvider);
    const preset = PROVIDERS.find((item) => item.value === nextProvider);
    if (!preset) return;
    setBaseUrl(preset.baseUrl);
    setModel(preset.model);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const nextSettings = await saveAISettings({
        provider,
        api_key: apiKey.trim() ? apiKey.trim() : undefined,
        base_url: baseUrl,
        model,
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

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/35 p-3 backdrop-blur-sm" onClick={onClose}>
      <form
        onSubmit={handleSave}
        className="flex h-full w-full max-w-lg animate-slide-up flex-col overflow-hidden rounded-lg bg-white shadow-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">KI-Einstellungen</p>
            <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Anbieter und API-Key</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {settings?.has_api_key ? `Aktiver Key: ${settings.masked_api_key}` : "Kein API-Key hinterlegt"}
            </p>
          </div>
          <button type="button" className="icon-btn" aria-label="Einstellungen schließen" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="grid flex-1 content-start gap-5 overflow-y-auto p-5">
          {loading ? (
            <div className="grid min-h-40 place-items-center text-sm font-bold text-slate-500">
              <span className="flex items-center gap-2">
                <span className="spinner" />
                Einstellungen werden geladen
              </span>
            </div>
          ) : (
            <>
              <div>
                <label className="label">Anbieter</label>
                <div className="segmented">
                  {PROVIDERS.map((item) => (
                    <button
                      key={item.value}
                      type="button"
                      aria-pressed={provider === item.value}
                      onClick={() => handleProviderChange(item.value)}
                      className={`segment ${provider === item.value ? "segment-active" : ""}`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="label" htmlFor="api-key">API key</label>
                <input
                  id="api-key"
                  className="input"
                  type="password"
                  placeholder={settings?.has_api_key ? "Leer lassen, um den aktuellen Key zu behalten" : "API-Key einfügen"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  autoComplete="off"
                />
              </div>

              <div>
                <label className="label" htmlFor="base-url">Basis-URL</label>
                <input
                  id="base-url"
                  className="input"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://openrouter.ai/api/v1"
                />
              </div>

              <div>
                <label className="label" htmlFor="model">Modell</label>
                <input
                  id="model"
                  className="input"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="openai/gpt-4o-mini"
                />
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
