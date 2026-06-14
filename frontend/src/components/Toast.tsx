"use client";

import { useState, useEffect, useCallback } from "react";

export interface ToastItem {
  id: string;
  type: "success" | "error" | "info";
  title: string;
  message?: string;
}

let toastId = 0;
let addToastFn: ((t: ToastItem) => void) | null = null;

export function showToast(type: ToastItem["type"], title: string, message?: string) {
  toastId++;
  addToastFn?.({ id: `toast-${toastId}`, type, title, message });
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  addToastFn = useCallback((t: ToastItem) => {
    setToasts((prev) => [...prev, t]);
  }, []);

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  if (toasts.length === 0) return null;

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
      setTimeout(() => onDismiss(item.id), 300);
    }, 4000);
    return () => clearTimeout(timer);
  }, [item.id, onDismiss]);

  const colorMap = {
    success: {
      bg: "bg-green-50/80 backdrop-blur-xl border-green-300/50",
      icon: "text-green-500",
      svg: "M5 13l4 4L19 7",
    },
    error: {
      bg: "bg-red-50/80 backdrop-blur-xl border-red-300/50",
      icon: "text-red-500",
      svg: "M6 18L18 6M6 6l12 12",
    },
    info: {
      bg: "bg-edeka-lightblue/80 backdrop-blur-xl border-edeka-blue/30",
      icon: "text-edeka-blue",
      svg: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    },
  };

  const style = colorMap[item.type];

  return (
    <div
      className={`toast flex items-start gap-3 px-4 py-3 rounded-xl border-2 shadow-glass-lg backdrop-blur-2xl
        min-w-[300px] max-w-[420px] cursor-pointer
        ${exiting ? "animate-toast-out" : "animate-toast-in"}
        ${style.bg}`}
      onClick={() => {
        setExiting(true);
        setTimeout(() => onDismiss(item.id), 300);
      }}
    >
      <svg className={`w-5 h-5 mt-0.5 flex-shrink-0 ${style.icon}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={style.svg} />
      </svg>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-bold text-gray-800">{item.title}</p>
        {item.message && <p className="text-xs text-gray-600 mt-0.5">{item.message}</p>}
      </div>
      <button className="text-gray-400 hover:text-gray-600 flex-shrink-0">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
