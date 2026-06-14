"use client";

import { useState, useEffect, useCallback } from "react";

export interface ToastItem {
  id: string;
  type: "success" | "error";
  title: string;
}

let toastId = 0;
let addToastFn: ((t: ToastItem) => void) | null = null;

export function showToast(type: ToastItem["type"], title: string) {
  toastId++;
  addToastFn?.({ id: `toast-${toastId}`, type, title });
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  addToastFn = useCallback((t: ToastItem) => {
    setToasts((prev) => [...prev, t]);
  }, []);

  const dismiss = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

  if (!toasts.length) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <ToastItem key={t.id} item={t} onDismiss={dismiss} />
      ))}
    </div>
  );
}

function ToastItem({ item, onDismiss }: { item: ToastItem; onDismiss: (id: string) => void }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setExiting(true);
      setTimeout(() => onDismiss(item.id), 250);
    }, 3000);
    return () => clearTimeout(timer);
  }, [item.id, onDismiss]);

  const isSuccess = item.type === "success";

  return (
    <div
      className={`toast flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium shadow-sm cursor-pointer
        ${exiting ? "animate-toast-out" : "animate-toast-in"}
        ${isSuccess ? "bg-green-50 border-green-200 text-green-700" : "bg-red-50 border-red-200 text-red-700"}`}
      onClick={() => {
        setExiting(true);
        setTimeout(() => onDismiss(item.id), 250);
      }}
    >
      <span>{isSuccess ? "✓" : "✗"}</span>
      {item.title}
    </div>
  );
}
