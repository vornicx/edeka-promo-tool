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
  { value: "lifestyle", label: "Foto Lifestyle", meta: "Natürlich" },
  { value: "magazine", label: "Magazin", meta: "Duoton" },
  { value: "retro", label: "Retro", meta: "Vintage" },
];

const TONES = [
  { value: "fresco", label: "Frisch" },
  { value: "premium", label: "Premium" },
  { value: "atrevido", label: "Mutig" },
  { value: "local", label: "Lokal" },
];

const FORMATS = [
  { value: "post", label: "Post", meta: "1:1" },
  { value: "story", label: "Story", meta: "9:16" },
  { value: "poster_a4", label: "A4", meta: "Plakat" },
  { value: "poster_a5", label: "A5", meta: "Plakat" },
];

const LEVELS = [
  { value: "bajo", label: "Dezent" },
  { value: "medio", label: "Ausgewogen" },
  { value: "alto", label: "Auffällig" },
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
      style: "colorblock",
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
    product_image: "",
    format: "post",
    style: "edeka",
    tone: "fresco",
    differentiation_level: "medio",
    use_ai_planning: false,
  });

  const errors = useMemo(() => validate(form), [form]);
  const valid = Object.keys(errors).length === 0;
  const isEvent = form.campaign_kind === "event";
  const isAiMode = form.use_ai_planning;

  const update = useCallback((field: keyof PromotionData, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  }, []);

  const chooseTemplateMode = () => {
    setForm((previous) => ({
      ...previous,
      campaign_kind: "product",
      use_ai_planning: false,
    }));
  };

  const chooseAiMode = () => {
    setForm((previous) => ({
      ...previous,
      use_ai_planning: true,
    }));
  };

  const chooseCampaignKind = (kind: "product" | "event") => {
    setForm((previous) => ({
      ...previous,
      campaign_kind: kind,
      category: kind === "event" ? "event" : previous.category === "event" ? "" : previous.category,
      old_price: kind === "event" ? "" : previous.old_price,
      product_image: kind === "event" ? "" : previous.product_image,
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
      });
    }, 220);
    return () => clearTimeout(t);
  }, [form.campaign_kind, form.product, form.price, form.old_price, form.validity, form.claim, form.origin, form.category, form.product_image]);

  const builtinMotifs = motifs.filter((m) => m.source === "builtin");
  const customMotifs = motifs.filter((m) => m.source === "custom");
  const selectedMotif = motifs.find((m) => m.value === form.product_image);

  const handleMotifChange = (value: string) => {
    setForm((previous) => {
      const motif = motifs.find((m) => m.value === value);
      const next: PromotionData = { ...previous, product_image: value };
      if (motif) {
        // Al elegir de la lista, sincroniza nombre y categoría automáticamente.
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
          Aktionsbriefing
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
                Plantillas
              </span>
              <span className="mt-2 block text-xs leading-5 text-slate-600">
                Para ofertas de producto. Rápido, estable y sin depender de IA.
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
                Para carteles promocionales de productos, Aktionen y eventos del mercado.
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

          <div className="grid gap-5 rounded-lg border border-slate-200 bg-slate-50/60 p-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-edeka-blue">Design und Ausgabe</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                {isAiMode
                  ? "Die KI nutzt diese Auswahl als Richtung und plant Farben, Komposition und Hierarchie passend dazu."
                  : "Die Vorauswahl funktioniert sofort. Ändere nur, wenn du einen anderen Look oder ein anderes Format brauchst."}
              </p>
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
        </section>
      </div>

      <div className="flex flex-col gap-3 border-t border-slate-200 bg-slate-50 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <p className="text-sm font-medium text-slate-600">
              Danach siehst du die fertige Vorschau und kannst das Bild speichern.
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
