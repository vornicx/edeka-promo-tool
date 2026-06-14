"use client";

import { useState } from "react";
import { PromotionData, CreativeDirection, createPromo } from "@/lib/api";

interface Props {
  onCreated: (sessionId: string, directions: CreativeDirection[]) => void;
}

const FORMATS = [
  { value: "post", label: "Instagram Post (1080x1080)" },
  { value: "story", label: "Instagram Story (1080x1920)" },
  { value: "poster_a4", label: "Poster A4" },
  { value: "poster_a5", label: "Poster A5" },
];

const TONES = [
  { value: "fresco", label: "Fresco" },
  { value: "premium", label: "Premium" },
  { value: "atrevido", label: "Atrevido" },
  { value: "local", label: "Local" },
];

const CATEGORIES = [
  "Fruta fresca",
  "Verdura",
  "Panadería",
  "Lácteos",
  "Carnes",
  "Pescados",
  "Bebidas",
  "Limpieza",
  "Hogar",
];

export default function PromoForm({ onCreated }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<PromotionData>({
    product: "",
    category: "",
    price: "",
    old_price: "",
    validity: "",
    origin: "",
    claim: "",
    format: "post",
    tone: "fresco",
    differentiation_level: "medio",
  });

  const update = (field: keyof PromotionData, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await createPromo(form);
      onCreated(result.session_id, result.directions);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al crear promoción");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="card space-y-4">
      <h2 className="text-2xl font-bold text-edeka-blue">Nueva Promoción</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Producto *</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: Fresas"
            value={form.product}
            onChange={(e) => update("product", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Categoría</label>
          <select
            className="input-field"
            value={form.category}
            onChange={(e) => update("category", e.target.value)}
          >
            <option value="">Seleccionar...</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c.toLowerCase()}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Precio *</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: 2,99 €"
            value={form.price}
            onChange={(e) => update("price", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Precio anterior</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: 4,99 €"
            value={form.old_price}
            onChange={(e) => update("old_price", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Vigencia *</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: Solo hoy"
            value={form.validity}
            onChange={(e) => update("validity", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Origen</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: España"
            value={form.origin}
            onChange={(e) => update("origin", e.target.value)}
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium mb-1">Claim</label>
          <input
            type="text"
            className="input-field"
            placeholder="Ej: Dulces y frescas"
            value={form.claim}
            onChange={(e) => update("claim", e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Formato</label>
          <select
            className="input-field"
            value={form.format}
            onChange={(e) => update("format", e.target.value)}
          >
            {FORMATS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Tono</label>
          <select
            className="input-field"
            value={form.tone}
            onChange={(e) => update("tone", e.target.value)}
          >
            {TONES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <button type="submit" className="btn-primary w-full" disabled={loading}>
        {loading ? "Generando direcciones creativas..." : "Crear Promoción"}
      </button>
    </form>
  );
}
