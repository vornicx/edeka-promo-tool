"use client";

import { useState, useCallback, useMemo } from "react";
import { PromotionData, CreativeDirection, createPromo } from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  onCreated: (sessionId: string, directions: CreativeDirection[]) => void;
}

const FORMATS = [
  { value: "post", label: "Instagram Post", detail: "1080\u00d71080 px" },
  { value: "story", label: "Instagram Story", detail: "1080\u00d71920 px" },
  { value: "poster_a4", label: "Póster A4", detail: "2480\u00d73508 px" },
  { value: "poster_a5", label: "Póster A5", detail: "1748\u00d72480 px" },
];

const TONES = [
  { value: "fresco", label: "Fresco", desc: "Cercano y natural" },
  { value: "premium", label: "Premium", desc: "Elegante y cuidado" },
  { value: "atrevido", label: "Atrevido", desc: "Directo y llamativo" },
  { value: "local", label: "Local", desc: "Cálido y de cercanía" },
];

const CATEGORIES = [
  "Fruta fresca", "Verdura", "Panadería", "Lácteos",
  "Carnes", "Pescados", "Bebidas", "Limpieza", "Hogar",
];

type FieldErrors = Partial<Record<keyof PromotionData, string>>;

function validate(form: PromotionData): FieldErrors {
  const errors: FieldErrors = {};
  if (!form.product.trim()) errors.product = "El producto es obligatorio";
  if (!form.price.trim()) errors.price = "El precio es obligatorio";
  else if (!/^[\d,.\s€$]+$/.test(form.price)) errors.price = "Precio inválido (ej: 2,99)";
  if (!form.validity.trim()) errors.validity = "La vigencia es obligatoria";
  return errors;
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

  const update = useCallback((field: keyof PromotionData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  }, []);

  const blur = useCallback((field: string) => {
    setTouched((prev) => new Set(prev).add(field));
  }, []);

  const fieldClass = (field: keyof PromotionData) => {
    if (!touched.has(field)) return "input-field";
    if (errors[field]) return "input-field error";
    if (form[field]?.toString().trim()) return "input-field success";
    return "input-field";
  };

  const isFormValid = useMemo(() => Object.keys(errors).length === 0, [errors]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const allFields: (keyof PromotionData)[] = ["product", "price", "validity"];
    setTouched(new Set(allFields));
    if (!isFormValid) {
      showToast("error", "Revisa los campos", "Corrige los errores antes de continuar");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const result = await createPromo(form);
      onCreated(result.session_id, result.directions);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al crear promoción";
      setError(msg);
      showToast("error", "Error", msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card-strong space-y-6">
      <div className="flex items-center gap-3 pb-2 border-b border-white/40">
        <div className="w-10 h-10 rounded-xl bg-edeka-blue/10 flex items-center justify-center">
          <svg className="w-5 h-5 text-edeka-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </div>
        <h2 className="text-xl font-extrabold text-edeka-blue drop-shadow-sm">Nueva Promoción</h2>
      </div>

      <div className="space-y-3">
        <h3 className="section-title">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          Datos del producto
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="input-label">
              Producto <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                className={fieldClass("product")}
                placeholder="Ej: Fresas de la región"
                value={form.product}
                onChange={(e) => update("product", e.target.value)}
                onBlur={() => blur("product")}
                required
              />
              <FieldIcon field="product" errors={errors} touched={touched} value={form.product} />
            </div>
            {touched.has("product") && errors.product && (
              <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.product}
              </p>
            )}
          </div>
          <div>
            <label className="input-label">Categoría</label>
            <select
              className="input-field"
              value={form.category}
              onChange={(e) => update("category", e.target.value)}
            >
              <option value="">Seleccionar...</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c.toLowerCase()}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="input-label">
              Precio <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                className={fieldClass("price")}
                placeholder="Ej: 2,99 €"
                value={form.price}
                onChange={(e) => update("price", e.target.value)}
                onBlur={() => blur("price")}
                required
              />
              <FieldIcon field="price" errors={errors} touched={touched} value={form.price} />
            </div>
            {touched.has("price") && errors.price && (
              <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.price}
              </p>
            )}
          </div>
          <div>
            <label className="input-label">Precio anterior (opcional)</label>
            <div className="relative">
              <input
                type="text"
                className="input-field"
                placeholder="Ej: 4,99 €"
                value={form.old_price}
                onChange={(e) => update("old_price", e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="input-label">
              Vigencia <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                className={fieldClass("validity")}
                placeholder="Ej: Solo hoy"
                value={form.validity}
                onChange={(e) => update("validity", e.target.value)}
                onBlur={() => blur("validity")}
                required
              />
              <FieldIcon field="validity" errors={errors} touched={touched} value={form.validity} />
            </div>
            {touched.has("validity") && errors.validity && (
              <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {errors.validity}
              </p>
            )}
          </div>
          <div>
            <label className="input-label">Origen (opcional)</label>
            <input
              type="text"
              className="input-field"
              placeholder="Ej: España"
              value={form.origin}
              onChange={(e) => update("origin", e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <label className="input-label">Claim (opcional)</label>
            <div className="relative">
              <input
                type="text"
                className="input-field pr-16"
                placeholder="Ej: Dulces y frescas como ninguna"
                value={form.claim}
                onChange={(e) => {
                  if (e.target.value.length <= 80) update("claim", e.target.value);
                }}
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 font-medium">
                {(form.claim || "").length}/80
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="section-title">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
          </svg>
          Estilo visual
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="input-label">Formato</label>
            <div className="grid grid-cols-2 gap-2">
              {FORMATS.map((f) => (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => update("format", f.value)}
                  className={`p-3 rounded-xl border-2 text-left transition-all duration-200 ${
                    form.format === f.value
                      ? "border-edeka-blue/50 bg-edeka-lightblue/60 backdrop-blur-sm shadow-sm ring-1 ring-edeka-blue/20"
                      : "border-white/40 bg-white/30 backdrop-blur-sm hover:bg-white/50 hover:border-white/60"
                  }`}
                >
                  <div className="text-sm font-bold">{f.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{f.detail}</div>
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="input-label">Tono visual</label>
            <div className="grid grid-cols-2 gap-2">
              {TONES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => update("tone", t.value)}
                  className={`p-3 rounded-xl border-2 text-left transition-all duration-200 ${
                    form.tone === t.value
                      ? "border-edeka-blue/50 bg-edeka-lightblue/60 backdrop-blur-sm shadow-sm ring-1 ring-edeka-blue/20"
                      : "border-white/40 bg-white/30 backdrop-blur-sm hover:bg-white/50 hover:border-white/60"
                  }`}
                >
                  <div className="text-sm font-bold">{t.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="animate-shake glass-strong border-red-300/40 text-red-700 text-sm font-medium flex items-center gap-3 p-4 rounded-xl">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}

      <button
        type="submit"
        className="btn-primary w-full flex items-center justify-center gap-3"
        disabled={loading}
      >
        {loading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Generando direcciones creativas...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Crear Promoción
          </>
        )}
      </button>
    </form>
  );
}

function FieldIcon({
  field,
  errors,
  touched,
  value,
}: {
  field: keyof PromotionData;
  errors: FieldErrors;
  touched: Set<string>;
  value: string;
}) {
  if (!touched.has(field)) return null;
  if (!value.trim()) return null;

  if (errors[field]) {
    return (
      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-red-400">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      </span>
    );
  }

  return (
    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500">
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    </span>
  );
}
