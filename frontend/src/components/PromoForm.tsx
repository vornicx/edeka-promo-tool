"use client";

import { useState, useMemo, useCallback } from "react";
import { PromotionData, CreativeDirection, createPromo } from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  onCreated: (sessionId: string, directions: CreativeDirection[]) => void;
}

const CATEGORIES = [
  "Fruta", "Verdura", "Panadería", "Lácteos",
  "Carnes", "Pescados", "Bebidas", "Hogar",
];

const TONES = [
  { value: "fresco", label: "🌿 Fresco" },
  { value: "premium", label: "✨ Premium" },
  { value: "atrevido", label: "🔥 Atrevido" },
  { value: "local", label: "🏡 Local" },
];

const FORMATS = [
  { value: "post", label: "Post 1:1" },
  { value: "story", label: "Story 9:16" },
  { value: "poster_a4", label: "A4" },
  { value: "poster_a5", label: "A5" },
];

type FieldErrors = Partial<Record<keyof PromotionData, string>>;

function validate(form: PromotionData): FieldErrors {
  const e: FieldErrors = {};
  if (!form.product.trim()) e.product = "Obligatorio";
  if (!form.price.trim()) e.price = "Obligatorio";
  else if (!/^[\d,.\s€$]+$/.test(form.price)) e.price = "Ej: 2,99";
  if (!form.validity.trim()) e.validity = "Obligatorio";
  return e;
}

export default function PromoForm({ onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const [form, setForm] = useState<PromotionData>({
    product: "", category: "", price: "", old_price: "",
    validity: "", origin: "", claim: "", format: "post",
    tone: "fresco", differentiation_level: "medio",
  });

  const errors = useMemo(() => validate(form), [form]);
  const valid = useMemo(() => Object.keys(errors).length === 0, [errors]);

  const update = useCallback((field: keyof PromotionData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  }, []);

  const blur = useCallback((field: string) => {
    setTouched((prev) => new Set(prev).add(field));
  }, []);

  const inputCls = (f: keyof PromotionData) =>
    `input-field${touched.has(f) && errors[f] ? " error" : ""}`;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(new Set(["product", "price", "validity"]));
    if (!valid) { showToast("error", "Revisa los campos"); return; }
    setLoading(true);
    setError("");
    try {
      const res = await createPromo(form);
      onCreated(res.session_id, res.directions);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="card space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="sm:col-span-2">
          <label className="input-label">Producto</label>
          <input
            type="text"
            className={inputCls("product")}
            placeholder="Ej: Fresas de la región"
            value={form.product}
            onChange={(e) => update("product", e.target.value)}
            onBlur={() => blur("product")}
          />
        </div>

        <div>
          <label className="input-label">Categoría</label>
          <select
            className="input-field"
            value={form.category}
            onChange={(e) => update("category", e.target.value)}
          >
            <option value="">Seleccionar</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c.toLowerCase()}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="input-label">Formato</label>
          <div className="flex gap-1.5">
            {FORMATS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => update("format", f.value)}
                className={`flex-1 py-1.5 px-2 rounded-lg border text-xs font-semibold transition-all ${
                  form.format === f.value
                    ? "border-edeka-blue bg-edeka-lightblue text-edeka-blue"
                    : "border-gray-200 text-gray-500 hover:border-gray-300"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="input-label">Precio</label>
          <input
            type="text"
            className={inputCls("price")}
            placeholder="2,99 €"
            value={form.price}
            onChange={(e) => update("price", e.target.value)}
            onBlur={() => blur("price")}
          />
        </div>

        <div>
          <label className="input-label">Antes (opc)</label>
          <input
            type="text"
            className="input-field"
            placeholder="4,99 €"
            value={form.old_price}
            onChange={(e) => update("old_price", e.target.value)}
          />
        </div>

        <div>
          <label className="input-label">Vigencia</label>
          <input
            type="text"
            className={inputCls("validity")}
            placeholder="Solo hoy"
            value={form.validity}
            onChange={(e) => update("validity", e.target.value)}
            onBlur={() => blur("validity")}
          />
        </div>

        <div>
          <label className="input-label">Origen (opc)</label>
          <input
            type="text"
            className="input-field"
            placeholder="España"
            value={form.origin}
            onChange={(e) => update("origin", e.target.value)}
          />
        </div>

        <div className="sm:col-span-2">
          <label className="input-label">Claim (opc)</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: Dulces y frescas como ninguna"
            value={form.claim}
            onChange={(e) => {
              if (e.target.value.length <= 80) update("claim", e.target.value);
            }}
          />
        </div>

        <div>
          <label className="input-label">Tono</label>
          <div className="flex gap-1.5 flex-wrap">
            {TONES.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => update("tone", t.value)}
                className={`py-1.5 px-3 rounded-lg border text-xs font-semibold transition-all ${
                  form.tone === t.value
                    ? "border-edeka-blue bg-edeka-lightblue text-edeka-blue"
                    : "border-gray-200 text-gray-500 hover:border-gray-300"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="animate-shake bg-red-50 border border-red-200 rounded-lg p-3 text-red-600 text-sm flex items-center gap-2">
          <span>⚠</span>
          {error}
        </div>
      )}

      <div className="flex justify-end pt-1">
        <button
          type="submit"
          className="btn-primary flex items-center gap-2"
          disabled={loading}
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generando...
            </>
          ) : (
            <>
              <span>🚀</span>
              Crear Promoción
            </>
          )}
        </button>
      </div>
    </form>
  );
}
