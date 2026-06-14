"use client";

import { useState, useMemo, useCallback } from "react";
import { PromotionData, CreativeDirection, createPromo } from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  onCreated: (sessionId: string, directions: CreativeDirection[]) => void;
}

const CATEGORIES = ["Fruta", "Verdura", "Panadería", "Lácteos", "Carnes", "Pescados", "Bebidas", "Hogar"];

const TONE = [
  { value: "fresco", label: "Fresco" },
  { value: "premium", label: "Premium" },
  { value: "atrevido", label: "Atrevido" },
  { value: "local", label: "Local" },
];

const FORMATS = [
  { value: "post", label: "Post" },
  { value: "story", label: "Story" },
  { value: "poster_a4", label: "A4" },
  { value: "poster_a5", label: "A5" },
];

function validate(f: PromotionData) {
  const e: Record<string, string> = {};
  if (!f.product.trim()) e.product = "Campo obligatorio";
  if (!f.price.trim()) e.price = "Campo obligatorio";
  else if (!/^[\d,.\s€$]+$/.test(f.price)) e.price = "Formato inválido";
  if (!f.validity.trim()) e.validity = "Campo obligatorio";
  return e;
}

export default function PromoForm({ onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const [form, setForm] = useState<PromotionData>({
    product: "", category: "", price: "", old_price: "",
    validity: "", origin: "", claim: "", format: "post",
    tone: "fresco", differentiation_level: "medio",
  });

  const errors = useMemo(() => validate(form), [form]);
  const valid = Object.keys(errors).length === 0;

  const upd = useCallback((f: keyof PromotionData, v: string) => setForm((p) => ({ ...p, [f]: v })), []);
  const cls = (f: keyof PromotionData) => `input${touched.has(f) && errors[f] ? " input-error" : ""}`;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(new Set(["product", "price", "validity"]));
    if (!valid) { showToast("error", "Revisa los campos"); return; }
    setLoading(true);
    try {
      const res = await createPromo(form);
      onCreated(res.session_id, res.directions);
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="card space-y-5">
      <div className="grid grid-cols-2 gap-x-4 gap-y-4">
        <div className="col-span-2">
          <label className="label">Producto</label>
          <input className={cls("product")} placeholder="ej. Fresas de la región"
            value={form.product} onChange={(e) => upd("product", e.target.value)}
            onBlur={() => setTouched((p) => new Set(p).add("product"))} />
        </div>

        <div>
          <label className="label">Categoría</label>
          <select className="input" value={form.category} onChange={(e) => upd("category", e.target.value)}>
            <option value="">Seleccionar</option>
            {CATEGORIES.map((c) => <option key={c} value={c.toLowerCase()}>{c}</option>)}
          </select>
        </div>

        <div>
          <label className="label">Formato</label>
          <div className="flex gap-1.5">
            {FORMATS.map((f) => (
              <button key={f.value} type="button" onClick={() => upd("format", f.value)}
                className={`flex-1 py-2 rounded-lg border text-xs font-semibold transition-all ${
                  form.format === f.value
                    ? "border-edeka-blue/30 bg-edeka-lightblue text-edeka-blue"
                    : "border-gray-100 text-gray-400 hover:border-gray-200"
                }`}>{f.label}</button>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Precio</label>
          <input className={cls("price")} placeholder="2,99 €"
            value={form.price} onChange={(e) => upd("price", e.target.value)}
            onBlur={() => setTouched((p) => new Set(p).add("price"))} />
        </div>

        <div>
          <label className="label">Antes</label>
          <input className="input" placeholder="4,99 €" value={form.old_price}
            onChange={(e) => upd("old_price", e.target.value)} />
        </div>

        <div>
          <label className="label">Vigencia</label>
          <input className={cls("validity")} placeholder="Solo hoy"
            value={form.validity} onChange={(e) => upd("validity", e.target.value)}
            onBlur={() => setTouched((p) => new Set(p).add("validity"))} />
        </div>

        <div>
          <label className="label">Origen</label>
          <input className="input" placeholder="España" value={form.origin}
            onChange={(e) => upd("origin", e.target.value)} />
        </div>

        <div className="col-span-2">
          <label className="label">Claim</label>
          <input className="input" placeholder="ej. Dulces y frescas como ninguna"
            value={form.claim} onChange={(e) => {
              if (e.target.value.length <= 80) upd("claim", e.target.value);
            }} />
        </div>

        <div>
          <label className="label">Tono</label>
          <div className="flex gap-1.5">
            {TONE.map((t) => (
              <button key={t.value} type="button" onClick={() => upd("tone", t.value)}
                className={`flex-1 py-2 rounded-lg border text-xs font-semibold transition-all ${
                  form.tone === t.value
                    ? "border-edeka-blue/30 bg-edeka-lightblue text-edeka-blue"
                    : "border-gray-100 text-gray-400 hover:border-gray-200"
                }`}>{t.label}</button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-1 border-t border-gray-50">
        <button type="submit" className="btn-primary mt-3" disabled={loading}>
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generando...
            </span>
          ) : "Crear promoción"}
        </button>
      </div>
    </form>
  );
}
