"use client";

import { useState } from "react";
import { exportPromo } from "@/lib/api";
import { showToast } from "@/components/Toast";

interface Props {
  sessionId: string | null;
  format: string;
  productName?: string;
}

const FORMAT_LABELS: Record<string, string> = {
  post: "Post 1:1",
  story: "Story 9:16",
  poster_a4: "Plakat A4",
  poster_a5: "Plakat A5",
};

function DownloadIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.7} d="M12 3v11m0 0l-4-4m4 4l4-4M5 19h14" />
    </svg>
  );
}

function slug(value: string): string {
  return (value || "promotion")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\w]+/g, "_")
    .replace(/^_+|_+$/g, "") || "promotion";
}

export default function ExportPanel({ sessionId, format, productName }: Props) {
  const [busy, setBusy] = useState(false);
  if (!sessionId) return null;

  const label = FORMAT_LABELS[format] ?? "Bild";

  const handleDownload = async () => {
    setBusy(true);
    try {
      const blob = await exportPromo(sessionId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `edeka_${slug(productName ?? "")}_${format}.png`;
      a.click();
      URL.revokeObjectURL(url);
      showToast("success", "Bild heruntergeladen");
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Download konnte nicht erstellt werden");
    } finally {
      setBusy(false);
    }
  };

  return (
    <button type="button" onClick={handleDownload} disabled={busy} className="btn-primary sm:w-auto">
      {busy ? (
        <span className="flex items-center gap-2">
          <span className="spinner" />
          Wird heruntergeladen
        </span>
      ) : (
        <span className="flex items-center gap-2">
          <DownloadIcon />
          Als {label} herunterladen
        </span>
      )}
    </button>
  );
}
