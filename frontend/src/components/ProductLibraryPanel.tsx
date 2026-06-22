"use client";

import { useEffect, useRef, useState } from "react";
import {
  CustomProduct,
  createProduct,
  deleteProduct,
  getProductImageUrl,
  listProducts,
} from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  open: boolean;
  onClose: () => void;
}

const CATEGORIES = [
  "Obst",
  "Gemüse",
  "Bäckerei",
  "Milchprodukte",
  "Fleisch",
  "Fisch",
  "Getränke",
  "Haushalt",
  "Sonstiges",
];

function CloseIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("Datei konnte nicht gelesen werden"));
    reader.readAsDataURL(file);
  });
}

export default function ProductLibraryPanel({ open, onClose }: Props) {
  const [products, setProducts] = useState<CustomProduct[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [dataUrl, setDataUrl] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = () => {
    setLoading(true);
    listProducts()
      .then(setProducts)
      .catch((err: unknown) =>
        showToast("error", err instanceof Error ? err.message : "Produkte konnten nicht geladen werden"),
      )
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (open) refresh();
  }, [open]);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      showToast("error", "Bitte eine Bilddatei auswählen");
      return;
    }
    try {
      setDataUrl(await readFileAsDataUrl(file));
      if (!name.trim()) setName(file.name.replace(/\.[^.]+$/, ""));
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Datei konnte nicht gelesen werden");
    }
  };

  const resetForm = () => {
    setName("");
    setCategory(CATEGORIES[0]);
    setDataUrl("");
    if (fileRef.current) fileRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      showToast("error", "Produktname eintragen");
      return;
    }
    if (!dataUrl) {
      showToast("error", "Bitte ein Produktfoto auswählen");
      return;
    }
    setSaving(true);
    try {
      await createProduct({ name: name.trim(), category, image_base64: dataUrl });
      showToast("success", "Produktvorlage gespeichert");
      resetForm();
      refresh();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Produkt konnte nicht gespeichert werden");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (product: CustomProduct) => {
    try {
      await deleteProduct(product.id);
      setProducts((prev) => prev.filter((p) => p.id !== product.id));
      showToast("success", "Produkt gelöscht");
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Produkt konnte nicht gelöscht werden");
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/35 p-3 backdrop-blur-sm" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-xl animate-slide-up flex-col overflow-hidden rounded-lg bg-white shadow-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 p-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Produkt-Bibliothek</p>
            <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Eigene Produkte</h2>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Lade ein Produktfoto hoch. Daraus entsteht eine wiederverwendbare Vorlage – wie bei Erdbeeren,
              Bananen & Co. Am besten ein Foto mit weißem oder transparentem Hintergrund.
            </p>
          </div>
          <button type="button" className="icon-btn" aria-label="Schließen" onClick={onClose}>
            <CloseIcon />
          </button>
        </div>

        <div className="grid flex-1 content-start gap-5 overflow-y-auto p-5">
          <form onSubmit={handleSubmit} className="grid gap-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-4">
              <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-lg border border-dashed border-slate-300 bg-white">
                {dataUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={dataUrl} alt="Vorschau" className="h-full w-full object-contain" />
                ) : (
                  <span className="px-2 text-center text-xs font-semibold text-slate-400">Keine Vorschau</span>
                )}
              </div>
              <div className="grid flex-1 gap-2">
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => handleFile(e.target.files?.[0])}
                />
                <button type="button" className="btn-ghost w-auto" onClick={() => fileRef.current?.click()}>
                  Foto auswählen
                </button>
                <p className="text-xs leading-5 text-slate-500">PNG oder JPG. Der Hintergrund wird automatisch entfernt.</p>
              </div>
            </div>

            <div>
              <label className="label" htmlFor="product-name">Produktname</label>
              <input
                id="product-name"
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="z. B. Gouda am Stück"
              />
            </div>

            <div>
              <label className="label" htmlFor="product-category">Kategorie</label>
              <select
                id="product-category"
                className="input"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <button type="submit" className="btn-primary w-auto justify-self-end" disabled={saving}>
              {saving ? (
                <span className="flex items-center gap-2">
                  <span className="spinner" />
                  Speichern
                </span>
              ) : (
                "Produktvorlage speichern"
              )}
            </button>
          </form>

          <div>
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-400">
              Gespeicherte Produkte ({products.length})
            </p>
            {loading ? (
              <div className="grid min-h-24 place-items-center text-sm font-bold text-slate-500">
                <span className="flex items-center gap-2"><span className="spinner" /> Wird geladen</span>
              </div>
            ) : products.length === 0 ? (
              <p className="rounded-lg border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                Noch keine eigenen Produkte. Lade oben dein erstes Produktfoto hoch.
              </p>
            ) : (
              <ul className="grid gap-2">
                {products.map((p) => (
                  <li key={p.id} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-2.5">
                    <div className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-md border border-slate-100 bg-slate-50">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={getProductImageUrl(p)} alt={p.name} className="h-full w-full object-contain" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold text-slate-900">{p.name}</p>
                      {p.category && <p className="text-xs font-medium text-slate-500">{p.category}</p>}
                    </div>
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label={`${p.name} löschen`}
                      onClick={() => handleDelete(p)}
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M6 7h12M9 7V5h6v2m-7 0v12a1 1 0 001 1h6a1 1 0 001-1V7" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="flex justify-end border-t border-slate-200 bg-slate-50 p-5">
          <button type="button" className="btn-primary w-auto" onClick={onClose}>
            Fertig
          </button>
        </div>
      </div>
    </div>
  );
}
