"use client";

import { useState, useEffect, useCallback } from "react";

export interface ToastItem {
  id: string;
  type: "success" | "error";
  title: string;
}

let id = 0;
let fn: ((t: ToastItem) => void) | null = null;

export function showToast(type: ToastItem["type"], title: string) {
  id++;
  fn?.({ id: `t-${id}`, type, title });
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  fn = useCallback((t: ToastItem) => setToasts((p) => [...p, t]), []);
  const dismiss = (d: string) => setToasts((p) => p.filter((t) => t.id !== d));

  if (!toasts.length) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <Item key={t.id} item={t} onDismiss={dismiss} />
      ))}
    </div>
  );
}

function Item({ item, onDismiss }: { item: ToastItem; onDismiss: (id: string) => void }) {
  const [ex, setEx] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => { setEx(true); setTimeout(() => onDismiss(item.id), 200); }, 2500);
    return () => clearTimeout(t);
  }, [item.id, onDismiss]);

  const ok = item.type === "success";

  return (
    <div onClick={() => { setEx(true); setTimeout(() => onDismiss(item.id), 200); }}
      className={`toast flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-semibold shadow-sm cursor-pointer
        ${ex ? "animate-toast-out" : "animate-toast-in"}
        ${ok ? "bg-white border-green-200 text-green-700" : "bg-white border-red-200 text-red-600"}`}>
      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold
        ${ok ? "bg-green-50 text-green-600" : "bg-red-50 text-red-500"}`}>
        {ok ? "✓" : "✗"}
      </span>
      {item.title}
    </div>
  );
}
