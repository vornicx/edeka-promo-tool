"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { showToast } from "@/components/Toast";
import {
  CreativeDirection,
  Motif,
  PromotionData,
  createPromo,
  exampleImageUrl,
  getMotifImageUrl,
  listMotifs,
} from "@/lib/api";
import { DesignPreset, useDesignPresets } from "@/lib/presets";

interface Props {
  onCreated: (
    sessionId: string,
    directions: CreativeDirection[],
    mode: string,
    note: string,
    format: string,
    product: string,
  ) => void;
}

const CATEGORIES = [
  { value: "event", label: "Event / Marktaktion" },
  { value: "verkostung", label: "Verkostung" },
  { value: "service", label: "Service" },
  { value: "obst", label: "Obst" },
  { value: "gemuese", label: "Gemüse" },
  { value: "baeckerei", label: "Bäckerei" },
  { value: "milchprodukte", label: "Milchprodukte" },
  { value: "kaese", label: "Käse" },
  { value: "bedientheke", label: "Bedientheke" },
  { value: "fleisch", label: "Fleisch" },
  { value: "fisch", label: "Fisch" },
  { value: "getraenke", label: "Getränke" },
  { value: "tiefkuehl", label: "Tiefkühl" },
  { value: "nudeln-sauce", label: "Nudeln & Sauce" },
  { value: "haushalt", label: "Haushalt" },
];

const STYLES = [
  { value: "edeka", label: "EDEKA Style", meta: "Knaller" },
  { value: "luxe", label: "Dark Luxe", meta: "Premium" },
  { value: "editorial", label: "Editorial", meta: "Hell & klar" },
  { value: "colorblock", label: "Color Block", meta: "Grafisch" },
  { value: "frischemarkt", label: "Frischemarkt", meta: "Frisch & klar" },
  { value: "prospekt", label: "Prospekt", meta: "Knüller" },
  { value: "markttafel", label: "Markt-Tafel", meta: "Tafel" },
  { value: "bio", label: "Bio / Natur", meta: "Natürlich" },
];

const TONES = [
  { value: "fresco", label: "Frisch", meta: "Klar & natürlich" },
  { value: "premium", label: "Premium", meta: "Edel, Gold, ruhig" },
  { value: "atrevido", label: "Mutig", meta: "Laut & kräftig" },
  { value: "local", label: "Lokal", meta: "Warm, aus der Region" },
];

const FORMATS = [
  { value: "post", label: "Post", meta: "1:1" },
  { value: "story", label: "Story", meta: "9:16" },
  { value: "poster_a4", label: "A4", meta: "Plakat" },
  { value: "poster_a5", label: "A5", meta: "Plakat" },
];

const LEVELS = [
  { value: "bajo", label: "Dezent", meta: "Ruhig & klein" },
  { value: "medio", label: "Ausgewogen", meta: "Standard" },
  { value: "alto", label: "Auffällig", meta: "Großer Preis" },
];

const PRICE_SIZES = [
  { value: "auto", label: "Auto", meta: "nach Niveau" },
  { value: "s", label: "S", meta: "klein" },
  { value: "m", label: "M", meta: "normal" },
  { value: "l", label: "L", meta: "groß" },
  { value: "xl", label: "XL", meta: "riesig" },
];

// Manual accent presets (EDEKA blue/yellow plus versatile retail tones).
const ACCENT_PRESETS = [
  { value: "#004C96", label: "Blau" },
  { value: "#E2001A", label: "Rot" },
  { value: "#3C8C2E", label: "Grün" },
  { value: "#CEA74E", label: "Gold" },
  { value: "#E8612C", label: "Orange" },
  { value: "#7A3E9D", label: "Beere" },
];

const QUICK_STARTS: Array<{ label: string; data: Partial<PromotionData> }> = [
  {
    label: "Erdbeeren",
    data: {
      product: "Erdbeeren aus der Region",
      campaign_kind: "product",
      category: "obst",
      price: "2,99 €",
      old_price: "3,99 €",
      validity: "Nur diese Woche",
      origin: "Deutschland",
      claim: "Süß und frisch",
      tone: "fresco",
      style: "edeka",
    },
  },
  {
    label: "Mövenpick Eis",
    data: {
      product: "Mövenpick Eis",
      campaign_kind: "product",
      category: "tiefkuehl",
      price: "1,79 €",
      old_price: "3,99 €",
      validity: "Nur diese Woche",
      claim: "Cremig sparen",
      product_image: "builtin:ice_cream_tub",
      tone: "premium",
      style: "luxe",
    },
  },
  {
    label: "Barilla Pasta",
    data: {
      product: "Barilla Pasta",
      campaign_kind: "product",
      category: "nudeln-sauce",
      price: "0,99 €",
      old_price: "1,99 €",
      validity: "Mo-Sa",
      claim: "Schnell auf dem Tisch",
      product_image: "builtin:pasta",
      tone: "local",
      style: "editorial",
    },
  },
  {
    label: "Sommerfest",
    data: {
      campaign_kind: "event",
      product: "Sommerfest im Markt",
      category: "event",
      price: "Eintritt frei",
      old_price: "",
      validity: "Samstag, 11-16 Uhr",
      origin: "EDEKA Mühlenbein",
      claim: "Probieren, sparen, gemeinsam feiern",
      product_image: "",
      tone: "local",
      style: "ai",
      use_ai_planning: true,
    },
  },
];

const CATEGORY_BY_LABEL = new Map(CATEGORIES.map((c) => [c.label, c.value]));

function validate(f: PromotionData) {
  const e: Record<string, string> = {};
  const isEvent = f.campaign_kind === "event";
  if (!f.product.trim()) e.product = isEvent ? "Titel eintragen" : "Produkt eintragen";
  if (!isEvent && !f.price.trim()) e.price = "Preis eintragen";
  else if (!isEvent && !/^[\d,.\s€$]+$/.test(f.price)) e.price = "Bitte ein gültiges Preisformat verwenden";
  if (!f.validity.trim()) e.validity = "Aktionszeitraum eintragen";
  return e;
}

export default function PromoForm({ onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const [motifs, setMotifs] = useState<Motif[]>([]);
  const [form, setForm] = useState<PromotionData>({
    campaign_kind: "product",
    product: "",
    category: "",
    price: "",
    old_price: "",
    validity: "",
    origin: "",
    claim: "",
    event_description: "",
    product_image: "",
    format: "post",
    style: "edeka",
    tone: "fresco",
    differentiation_level: "medio",
    accent_color: "",
    price_size: "auto",
    use_ai_planning: false,
  });

  const errors = useMemo(() => validate(form), [form]);
  const valid = Object.keys(errors).length === 0;
  const isEvent = form.campaign_kind === "event";
  const isAiMode = form.use_ai_planning;
  const accentIsPreset = ACCENT_PRESETS.some((c) => c.value.toLowerCase() === (form.accent_color || "").toLowerCase());
  const accentIsCustom = Boolean(form.accent_color) && !accentIsPreset;

  const { presets, addPreset, removePreset } = useDesignPresets();
  const [savingPreset, setSavingPreset] = useState(false);
  const [presetName, setPresetName] = useState("");

  const applyPreset = (p: DesignPreset) => {
    setForm((previous) => ({
      ...previous,
      style: p.style,
      tone: p.tone,
      differentiation_level: p.differentiation_level,
      accent_color: p.accent_color || "",
      price_size: p.price_size || "auto",
    }));
  };

  const saveCurrentPreset = () => {
    const name = presetName.trim();
    if (!name) return;
    addPreset({
      name,
      style: form.style,
      tone: form.tone,
      differentiation_level: form.differentiation_level,
      accent_color: form.accent_color || "",
      price_size: form.price_size || "auto",
    });
    setPresetName("");
    setSavingPreset(false);
  };

  const update = useCallback((field: keyof PromotionData, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  }, []);

  const chooseTemplateMode = () => {
    setForm((previous) => ({
      ...previous,
      campaign_kind: "product",
      use_ai_planning: false,
      style: previous.style === "ai" ? "edeka" : previous.style,
    }));
  };

  const chooseAiMode = () => {
    setForm((previous) => ({
      ...previous,
      use_ai_planning: true,
      style: "ai",
      tone: previous.tone || "local",
    }));
  };

  const chooseCampaignKind = (kind: "product" | "event") => {
    setForm((previous) => ({
      ...previous,
      campaign_kind: kind,
      category: kind === "event" ? "event" : previous.category === "event" ? "" : previous.category,
      old_price: kind === "event" ? "" : previous.old_price,
      product_image: kind === "event" ? "" : previous.product_image,
      style: previous.use_ai_planning ? "ai" : previous.style,
    }));
  };

  const loadMotifs = useCallback(() => {
    listMotifs()
      .then(setMotifs)
      .catch(() => {
        /* el selector simplemente queda en "Automatisch" */
      });
  }, []);

  useEffect(() => {
    loadMotifs();
  }, [loadMotifs]);

  // Debounced snapshot of the briefing so example thumbnails mirror the real
  // promotion without re-fetching on every keystroke.
  const [exampleCtx, setExampleCtx] = useState({
    campaign_kind: "product" as "product" | "event",
    product: "",
    price: "",
    old_price: "",
    validity: "",
    claim: "",
    origin: "",
    category: "",
    product_image: "",
    accent_color: "",
    price_size: "auto",
  });
  useEffect(() => {
    const t = setTimeout(() => {
      setExampleCtx({
        campaign_kind: form.campaign_kind,
        product: form.product,
        price: form.price,
        old_price: form.old_price || "",
        validity: form.validity,
        claim: form.claim || "",
        origin: form.origin || "",
        category: form.category || "",
        product_image: form.product_image || "",
        accent_color: form.accent_color || "",
        price_size: form.price_size || "auto",
      });
    }, 220);
    return () => clearTimeout(t);
  }, [form.campaign_kind, form.product, form.price, form.old_price, form.validity, form.claim, form.origin, form.category, form.product_image, form.accent_color, form.price_size]);

  const builtinMotifs = motifs.filter((m) => m.source === "builtin");
  const customMotifs = motifs.filter((m) => m.source === "custom");
  const selectedMotif = motifs.find((m) => m.value === form.product_image);

  const handleMotifChange = (value: string) => {
    setForm((previous) => {
      const motif = motifs.find((m) => m.value === value);
      const next: PromotionData = { ...previous, product_image: value };
      if (motif) {
        // Beim Auswählen aus der Liste werden Name und Kategorie automatisch übernommen.
        next.campaign_kind = "product";
        next.product = motif.name;
        next.category = motif.category ? (CATEGORY_BY_LABEL.get(motif.category) ?? "") : previous.category;
      }
      return next;
    });
  };

  const applyQuickStart = (data: Partial<PromotionData>) => {
    setForm((previous) => ({
      ...previous,
      product_image: "",
      format: "post",
      differentiation_level: "medio",
      ...data,
    }));
    setTouched(new Set());
  };

  const renderExampleCards = (
    options: { value: string; label: string; meta?: string }[],
    current: string,
    onPick: (value: string) => void,
    urlFor: (value: string) => string,
    cols: string,
    fit: "cover" | "contain" = "cover",
  ) => (
    <div className={`grid gap-2.5 ${cols}`}>
      {options.map((o) => {
        const active = current === o.value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={active}
            onClick={() => onPick(o.value)}
            className={`group relative overflow-hidden rounded-xl border text-left transition-all ${
              active
                ? "border-edeka-blue ring-2 ring-edeka-blue/25 shadow-brand"
                : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-edeka-blue/40 hover:shadow-card"
            }`}
          >
            <div className="relative aspect-square w-full bg-slate-100">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={urlFor(o.value)}
                alt={o.label}
                loading="lazy"
                className={`h-full w-full ${fit === "contain" ? "object-contain p-1" : "object-cover"}`}
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
              <p className={`text-xs font-bold ${active ? "text-edeka-blue" : "text-slate-900"}`}>{o.label}</p>
              {o.meta && <p className="text-[10px] font-medium text-slate-500">{o.meta}</p>}
            </div>
          </button>
        );
      })}
    </div>
  );

  const markTouched = (field: keyof PromotionData) => {
    setTouched((previous) => new Set(previous).add(field));
  };

  const inputClass = (field: keyof PromotionData) => `input${touched.has(field) && errors[field] ? " input-error" : ""}`;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(new Set(["product", "price", "validity"]));
    if (!valid) {
      showToast("error", "Bitte Pflichtfelder prüfen");
      return;
    }

    setLoading(true);
    try {
      const res = await createPromo(form);
      onCreated(res.session_id, res.directions, res.generation_mode, res.generation_note, form.format, form.product);
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Promotion konnte nicht erstellt werden");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="panel overflow-hidden border-t-4 border-edeka-yellow">
      <div className="border-b border-slate-200 bg-white p-5 sm:p-6">
        <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">
          <span className="h-3 w-1.5 rounded-full bg-edeka-yellow" />
          Aktionsangaben
        </p>
        <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-950">
              {isEvent ? "Event eintragen" : "Angebot eintragen"}
            </h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
              {isEvent
                ? "Für Events reichen Titel, Termin und ein kurzer Hinweis. Die KI plant daraus ein klares Markt-Plakat."
                : "Nur drei Angaben sind nötig: Produkt, Preis und Zeitraum. Alles andere ist optional."}
            </p>
          </div>
          <span className="rounded-lg bg-edeka-lightblue px-3 py-2 text-xs font-bold text-edeka-blue">
            {Object.keys(errors).length === 0 ? "Briefing vollständig" : isEvent ? "2 Pflichtfelder" : "3 Pflichtfelder"}
          </span>
        </div>
      </div>

      <div className="grid gap-6 p-5 sm:p-6">
        <section className="rounded-lg border border-edeka-blue/15 bg-edeka-lightblue/60 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Schnellstart</p>
              <p className="mt-1 text-sm font-semibold text-slate-700">Beispiel übernehmen und anpassen.</p>
            </div>
            <div className="grid gap-2 sm:grid-cols-4">
              {QUICK_STARTS.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  className="rounded-lg bg-white px-3 py-2 text-sm font-extrabold text-edeka-blue shadow-sm transition-colors hover:bg-edeka-yellow focus:outline-none focus:ring-4 focus:ring-edeka-blue/15"
                  onClick={() => applyQuickStart(item.data)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Erstellungsart</p>
            <p className="mt-1 text-sm font-semibold text-slate-700">Wähle zuerst, wie das Motiv entstehen soll.</p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <button
              type="button"
              className={`rounded-lg border p-4 text-left transition-all ${!isAiMode ? "border-edeka-blue bg-edeka-lightblue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white hover:border-edeka-blue/35"}`}
              onClick={chooseTemplateMode}
              aria-pressed={!isAiMode}
            >
              <span className="flex items-center gap-2 text-sm font-extrabold text-edeka-blue">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zm10-2a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1v-5z" />
                </svg>
                Vorlagen
              </span>
              <span className="mt-2 block text-xs leading-5 text-slate-600">
                Für Produktangebote. Schnell, zuverlässig und ohne KI-Abhängigkeit.
              </span>
            </button>
            <button
              type="button"
              className={`rounded-lg border p-4 text-left transition-all ${isAiMode ? "border-edeka-blue bg-edeka-lightblue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white hover:border-edeka-blue/35"}`}
              onClick={chooseAiMode}
              aria-pressed={isAiMode}
            >
              <span className="flex items-center gap-2 text-sm font-extrabold text-edeka-blue">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9.75 3.104v5.469a4.5 4.5 0 01-1.348 3.677C5.62 15.032 3 17.613 3 20.75c0 1.325.219 2.59.622 3.75h16.756A9.75 9.75 0 0021 20.75c0-3.137-2.62-5.718-5.402-8.5A4.5 4.5 0 0114.25 8.573V3.104" />
                </svg>
                IA
              </span>
              <span className="mt-2 block text-xs leading-5 text-slate-600">
                Für KI-gestaltete Produktplakate, Marktaktionen und Veranstaltungen.
              </span>
            </button>
          </div>
          {isAiMode && (
            <div className="grid gap-2">
              <label className="label mb-0">Was soll die KI gestalten?</label>
              <div className="segmented">
                <button type="button" className={`segment ${!isEvent ? "segment-active" : ""}`} onClick={() => chooseCampaignKind("product")}>
                  Produktangebot
                </button>
                <button type="button" className={`segment ${isEvent ? "segment-active" : ""}`} onClick={() => chooseCampaignKind("event")}>
                  Event / Aktion
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="label" htmlFor="product">{isEvent ? "Titel *" : "Produkt *"}</label>
            <input
              id="product"
              className={inputClass("product")}
              placeholder={isEvent ? "z. B. Sommerfest im Markt" : "z. B. Erdbeeren aus der Region"}
              value={form.product}
              onChange={(e) => update("product", e.target.value)}
              onBlur={() => markTouched("product")}
            />
            {touched.has("product") && errors.product && <p className="field-error">{errors.product}</p>}
          </div>

          {!isEvent && (
          <div className="md:col-span-2">
            <label className="label" htmlFor="motif">Produktbild / Motiv</label>
            <div className="flex items-center gap-3">
              <div className="grid h-12 w-12 shrink-0 place-items-center overflow-hidden rounded-md border border-slate-200 bg-slate-50">
                {selectedMotif ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={getMotifImageUrl(selectedMotif)} alt={selectedMotif.name} className="h-full w-full object-contain" />
                ) : (
                  <span className="text-[10px] font-bold uppercase tracking-wide text-slate-400">Auto</span>
                )}
              </div>
              <select
                id="motif"
                className="input"
                value={form.product_image}
                onChange={(e) => handleMotifChange(e.target.value)}
                onFocus={loadMotifs}
              >
                <option value="">Automatisch (nach Produktname)</option>
                {builtinMotifs.length > 0 && (
                  <optgroup label="Integrierte Motive">
                    {builtinMotifs.map((m) => (
                      <option key={m.value} value={m.value}>{m.name}</option>
                    ))}
                  </optgroup>
                )}
                {customMotifs.length > 0 && (
                  <optgroup label="Eigene Fotos">
                    {customMotifs.map((m) => (
                      <option key={m.value} value={m.value}>{m.name}</option>
                    ))}
                  </optgroup>
                )}
              </select>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Kann leer bleiben. Dann wählt das Studio ein passendes Motiv anhand des Produktnamens.
            </p>
          </div>
          )}

          <div>
            <label className="label" htmlFor="category">{isEvent ? "Art der Aktion" : "Kategorie"}</label>
            <select
              id="category"
              className="input"
              value={form.category}
              onChange={(e) => update("category", e.target.value)}
            >
              <option value="">Kategorie auswählen</option>
              {CATEGORIES.map((category) => (
                <option key={category.value} value={category.value}>{category.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label" htmlFor="price">{isEvent ? "Hinweis / Highlight" : "Preis *"}</label>
            <input
              id="price"
              className={inputClass("price")}
              placeholder={isEvent ? "z. B. Eintritt frei, Verkostung, 11-16 Uhr" : "2,99 €"}
              value={form.price}
              onChange={(e) => update("price", e.target.value)}
              onBlur={() => markTouched("price")}
            />
            {touched.has("price") && errors.price && <p className="field-error">{errors.price}</p>}
          </div>

          {!isEvent && (
          <div>
            <label className="label" htmlFor="old-price">Alter Preis</label>
            <input
              id="old-price"
              className="input"
              placeholder="4,99 €"
              value={form.old_price}
              onChange={(e) => update("old_price", e.target.value)}
            />
          </div>
          )}

          <div>
            <label className="label" htmlFor="validity">{isEvent ? "Termin / Zeitraum *" : "Aktionszeitraum *"}</label>
            <input
              id="validity"
              className={inputClass("validity")}
              placeholder={isEvent ? "z. B. Samstag, 11-16 Uhr" : "Nur heute, Mo-Sa oder bis 30.06."}
              value={form.validity}
              onChange={(e) => update("validity", e.target.value)}
              onBlur={() => markTouched("validity")}
            />
            {touched.has("validity") && errors.validity && <p className="field-error">{errors.validity}</p>}
          </div>

          <div>
            <label className="label" htmlFor="origin">{isEvent ? "Ort / Bereich" : "Herkunft"}</label>
            <input
              id="origin"
              className="input"
              placeholder={isEvent ? "z. B. Getränkemarkt, Bedientheke" : "z. B. Deutschland"}
              value={form.origin}
              onChange={(e) => update("origin", e.target.value)}
            />
          </div>
        </section>

        <section className="grid gap-4 border-t border-slate-200 pt-6">
          <div>
            <div className="flex items-center justify-between gap-3">
              <label className="label mb-0" htmlFor="claim">Kurzer Werbesatz</label>
              <span className="text-xs font-semibold text-slate-400">{form.claim?.length || 0}/80</span>
            </div>
            <input
              id="claim"
              className="input mt-1.5"
              placeholder="z. B. Süß und frisch"
              value={form.claim}
              onChange={(e) => {
                if (e.target.value.length <= 80) update("claim", e.target.value);
              }}
            />
          </div>

          {isEvent && (
          <div>
            <div className="flex items-center justify-between gap-3">
              <label className="label mb-0" htmlFor="event_description">Event-Beschreibung</label>
              <span className="text-xs font-semibold text-slate-400">{(form.event_description || "").length}/300</span>
            </div>
            <textarea
              id="event_description"
              className="input mt-1.5 min-h-24 resize-y"
              placeholder="Was passiert? Wer kommt? Welche Stimmung? z.B. 'Weinverkostung mit Winzer aus der Pfalz, Live-Musik und regionale Spezialitäten. Exklusive Abendveranstaltung für Genießer.'"
              value={form.event_description || ""}
              onChange={(e) => {
                if (e.target.value.length <= 300) update("event_description", e.target.value);
              }}
            />
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Je detailreicher, desto passgenauer das KI-Design. Beschreibe Stimmung, Zielgruppe, Besonderheiten.
            </p>
          </div>
          )}

          {!isAiMode ? (
          <div className="grid gap-5 rounded-lg border border-slate-200 bg-slate-50/60 p-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Design und Ausgabe</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Die Vorauswahl funktioniert sofort. Ändern Sie nur, wenn Sie einen anderen Look oder ein anderes Format benötigen.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between gap-2">
                <label className="label mb-0">Design-Presets</label>
                {!savingPreset && (
                  <button
                    type="button"
                    onClick={() => setSavingPreset(true)}
                    className="text-xs font-bold text-edeka-blue hover:underline"
                  >
                    + Aktuelles Design sichern
                  </button>
                )}
              </div>

              {savingPreset && (
                <div className="mt-2 flex items-center gap-2">
                  <input
                    autoFocus
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") { e.preventDefault(); saveCurrentPreset(); }
                      if (e.key === "Escape") { setSavingPreset(false); setPresetName(""); }
                    }}
                    placeholder="Name des Presets"
                    maxLength={28}
                    className="input h-10 flex-1"
                  />
                  <button
                    type="button"
                    onClick={saveCurrentPreset}
                    disabled={!presetName.trim()}
                    className="rounded-lg bg-edeka-blue px-3 py-2 text-xs font-extrabold text-white transition-opacity disabled:opacity-40"
                  >
                    Sichern
                  </button>
                  <button
                    type="button"
                    onClick={() => { setSavingPreset(false); setPresetName(""); }}
                    className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-500 hover:bg-slate-100"
                  >
                    Abbrechen
                  </button>
                </div>
              )}

              <div className="mt-2 flex flex-wrap gap-2">
                {presets.length === 0 && (
                  <p className="text-xs text-slate-400">Noch keine Presets — sichern Sie Ihr Lieblingsdesign.</p>
                )}
                {presets.map((p) => {
                  const active =
                    form.style === p.style &&
                    form.tone === p.tone &&
                    form.differentiation_level === p.differentiation_level &&
                    (form.accent_color || "") === (p.accent_color || "") &&
                    (form.price_size || "auto") === (p.price_size || "auto");
                  return (
                    <span
                      key={p.id}
                      className={`group inline-flex items-center rounded-pill border py-1 pl-1 pr-0.5 text-xs font-bold transition-colors ${
                        active
                          ? "border-edeka-blue bg-edeka-lightblue text-edeka-blue"
                          : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/40"
                      }`}
                    >
                      <button type="button" onClick={() => applyPreset(p)} className="inline-flex items-center gap-1.5 pl-1.5 pr-1">
                        <span
                          className="h-3 w-3 shrink-0 rounded-full border border-black/10"
                          style={
                            p.accent_color
                              ? { backgroundColor: p.accent_color }
                              : { background: "conic-gradient(from 90deg, #E2001A, #FFD600, #3C8C2E, #0EA5E9, #7A3E9D, #E2001A)" }
                          }
                        />
                        {p.name}
                      </button>
                      <button
                        type="button"
                        aria-label={`${p.name} löschen`}
                        onClick={() => removePreset(p.id)}
                        className="grid h-5 w-5 place-items-center rounded-full text-slate-300 hover:bg-black/5 hover:text-red-600"
                      >
                        <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 6l12 12M18 6L6 18" />
                        </svg>
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="label">Designstil</label>
              {renderExampleCards(
                STYLES,
                form.style,
                (v) => update("style", v),
                (v) => exampleImageUrl({ ...exampleCtx, style: v, tone: form.tone, level: form.differentiation_level, format: "post" }),
                "grid-cols-2 sm:grid-cols-4",
              )}
            </div>

            <div>
              <label className="label">Tonalität</label>
              {renderExampleCards(
                TONES,
                form.tone,
                (v) => update("tone", v),
                (v) => exampleImageUrl({ ...exampleCtx, style: form.style, tone: v, level: form.differentiation_level, format: "post" }),
                "grid-cols-2 sm:grid-cols-4",
              )}
            </div>

            <div>
              <label className="label">Kreativniveau</label>
              {renderExampleCards(
                LEVELS,
                form.differentiation_level,
                (v) => update("differentiation_level", v),
                (v) => exampleImageUrl({ ...exampleCtx, style: form.style, tone: form.tone, level: v, format: "post" }),
                "grid-cols-3",
              )}
            </div>

            <div>
              <label className="label">Preisgröße</label>
              {renderExampleCards(
                PRICE_SIZES,
                form.price_size || "auto",
                (v) => update("price_size", v),
                (v) => exampleImageUrl({ ...exampleCtx, style: form.style, tone: form.tone, level: form.differentiation_level, format: "post", price_size: v }),
                "grid-cols-5",
              )}
              <p className="mt-1.5 text-[11px] leading-4 text-slate-500">Unabhängig vom Kreativniveau — steuert nur die Größe des Preises.</p>
            </div>

            <div>
              <label className="label">Akzentfarbe</label>
              <div className="flex flex-wrap items-center gap-2.5">
                <button
                  type="button"
                  title="Automatisch aus dem Produkt"
                  aria-label="Automatisch"
                  aria-pressed={!form.accent_color}
                  onClick={() => update("accent_color", "")}
                  className={`h-9 w-9 rounded-full border border-black/10 transition ${!form.accent_color ? "ring-2 ring-edeka-blue ring-offset-2 ring-offset-slate-50" : "hover:scale-105"}`}
                  style={{ background: "conic-gradient(from 90deg, #E2001A, #FFD600, #3C8C2E, #0EA5E9, #7A3E9D, #E2001A)" }}
                />
                {ACCENT_PRESETS.map((c) => {
                  const active = (form.accent_color || "").toLowerCase() === c.value.toLowerCase();
                  return (
                    <button
                      key={c.value}
                      type="button"
                      title={c.label}
                      aria-label={c.label}
                      aria-pressed={active}
                      onClick={() => update("accent_color", c.value)}
                      className={`h-9 w-9 rounded-full border border-black/10 transition ${active ? "ring-2 ring-edeka-blue ring-offset-2 ring-offset-slate-50" : "hover:scale-105"}`}
                      style={{ backgroundColor: c.value }}
                    />
                  );
                })}
                <label
                  title="Eigene Farbe wählen"
                  className={`relative grid h-9 w-9 cursor-pointer place-items-center rounded-full transition hover:scale-105 ${accentIsCustom ? "border border-black/10 ring-2 ring-edeka-blue ring-offset-2 ring-offset-slate-50" : "border-2 border-dashed border-slate-300 text-slate-400 hover:border-edeka-blue/50 hover:text-edeka-blue"}`}
                  style={accentIsCustom ? { backgroundColor: form.accent_color } : undefined}
                >
                  {!accentIsCustom && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v14M5 12h14" />
                    </svg>
                  )}
                  <input
                    type="color"
                    value={form.accent_color || "#004C96"}
                    onChange={(e) => update("accent_color", e.target.value)}
                    className="absolute inset-0 cursor-pointer opacity-0"
                    aria-label="Eigene Akzentfarbe"
                  />
                </label>
                <span className="ml-1 text-[11px] font-bold uppercase tracking-wide text-slate-400">
                  {form.accent_color ? form.accent_color.toUpperCase() : "Auto"}
                </span>
              </div>
              <p className="mt-2 text-[11px] leading-4 text-slate-500">
                {form.accent_color ? "Diese Farbe überschreibt den Akzent in allen Stilen." : "Auto: Akzent kommt automatisch aus dem Produktfoto."}
              </p>
            </div>

            <div>
              <label className="label">Format</label>
              {renderExampleCards(
                FORMATS,
                form.format,
                (v) => update("format", v),
                (v) => exampleImageUrl({ ...exampleCtx, style: form.style, tone: form.tone, level: form.differentiation_level, format: v }),
                "grid-cols-2 sm:grid-cols-4",
                "contain",
              )}
            </div>
          </div>
          ) : (
          <div className="grid gap-5 rounded-lg border border-edeka-blue/20 bg-edeka-lightblue/50 p-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">KI-Angaben</p>
              <p className="mt-1 text-xs leading-5 text-slate-600">
                Keine Vorlage auswählen. Bei Events erzeugt die KI ein reales Bildmotiv aus Titel, Termin, Ort und Beschreibung.
              </p>
            </div>

            <div>
              <label className="label">Art des KI-Plakats</label>
              <div className="grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  className={`rounded-lg border px-3 py-3 text-left text-sm font-extrabold transition-all ${!isEvent ? "border-edeka-blue bg-white text-edeka-blue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/35"}`}
                  onClick={() => chooseCampaignKind("product")}
                >
                  Produktangebot
                  <span className="mt-1 block text-xs font-semibold leading-5 text-slate-500">Produkt, Preis, Aktionszeitraum</span>
                </button>
                <button
                  type="button"
                  className={`rounded-lg border px-3 py-3 text-left text-sm font-extrabold transition-all ${isEvent ? "border-edeka-blue bg-white text-edeka-blue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/35"}`}
                  onClick={() => chooseCampaignKind("event")}
                >
                  Event / Marktaktion
                  <span className="mt-1 block text-xs font-semibold leading-5 text-slate-500">Titel, Termin, Ort, Highlight</span>
                </button>
              </div>
            </div>

            <div>
              <label className="label">Richtung</label>
              <div className="grid gap-2 sm:grid-cols-4">
                {TONES.map((tone) => (
                  <button
                    key={tone.value}
                    type="button"
                    className={`rounded-lg border px-3 py-2 text-sm font-extrabold transition-all ${form.tone === tone.value ? "border-edeka-blue bg-white text-edeka-blue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/35"}`}
                    onClick={() => update("tone", tone.value)}
                  >
                    {tone.label}
                    <span className="mt-0.5 block text-[11px] font-semibold leading-4 text-slate-400">{tone.meta}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Ausdruck</label>
              <div className="grid gap-2 sm:grid-cols-3">
                {LEVELS.map((level) => (
                  <button
                    key={level.value}
                    type="button"
                    className={`rounded-lg border px-3 py-2 text-sm font-extrabold transition-all ${form.differentiation_level === level.value ? "border-edeka-blue bg-white text-edeka-blue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/35"}`}
                    onClick={() => update("differentiation_level", level.value)}
                  >
                    {level.label}
                    <span className="mt-0.5 block text-[11px] font-semibold leading-4 text-slate-400">{level.meta}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Format</label>
              <div className="grid gap-2 sm:grid-cols-4">
                {FORMATS.map((format) => (
                  <button
                    key={format.value}
                    type="button"
                    className={`rounded-lg border px-3 py-2 text-left text-sm font-extrabold transition-all ${form.format === format.value ? "border-edeka-blue bg-white text-edeka-blue ring-2 ring-edeka-blue/20" : "border-slate-200 bg-white text-slate-700 hover:border-edeka-blue/35"}`}
                    onClick={() => update("format", format.value)}
                  >
                    {format.label}
                    <span className="block text-xs font-semibold text-slate-500">{format.meta}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
          )}
        </section>
      </div>

      <div className="flex flex-col gap-3 border-t border-slate-200 bg-slate-50 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <p className="text-sm font-medium text-slate-600">
              Danach sehen Sie die fertige Vorschau und können das Bild speichern.
        </p>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="spinner" />
              Wird erstellt
            </span>
          ) : (
            isEvent ? "Event-Plakat erstellen" : isAiMode ? "KI-Promotion erstellen" : "Promotion erstellen"
          )}
        </button>
      </div>
    </form>
  );
}
