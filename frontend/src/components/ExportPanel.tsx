"use client";

import { useEffect, useState } from "react";
import { exportPromo, exportPromoPdf, exportPromoZip } from "@/lib/api";
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

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ExportPanel({ sessionId, format, productName }: Props) {
  const [busy, setBusy] = useState<"" | "png" | "zip" | "pdf" | "share">("");
  const [canShare, setCanShare] = useState(false);

  // navigator.share mit Dateien gibt es nur auf Mobilgeräten/HTTPS.
  useEffect(() => {
    const nav = navigator as Navigator & { canShare?: (data: { files: File[] }) => boolean };
    try {
      const probe = new File([""], "probe.png", { type: "image/png" });
      setCanShare(Boolean(nav.canShare?.({ files: [probe] })));
    } catch {
      setCanShare(false);
    }
  }, []);

  if (!sessionId) return null;

  const label = FORMAT_LABELS[format] ?? "Bild";
  const base = `edeka_${slug(productName ?? "")}`;

  const run = async (kind: "png" | "zip" | "pdf" | "share", fn: () => Promise<void>) => {
    setBusy(kind);
    try {
      await fn();
    } catch (err: unknown) {
      showToast("error", err instanceof Error ? err.message : "Download konnte nicht erstellt werden");
    } finally {
      setBusy("");
    }
  };

  const handleDownload = () =>
    run("png", async () => {
      saveBlob(await exportPromo(sessionId, format), `${base}_${format}.png`);
      showToast("success", "Bild heruntergeladen");
    });

  const handleZip = () =>
    run("zip", async () => {
      saveBlob(await exportPromoZip(sessionId), `${base}_alle_formate.zip`);
      showToast("success", "Alle Formate heruntergeladen");
    });

  const handlePdf = () =>
    run("pdf", async () => {
      const pdfFormat = format.startsWith("poster") ? format : "poster_a4";
      saveBlob(await exportPromoPdf(sessionId, pdfFormat), `${base}_${pdfFormat}.pdf`);
      showToast("success", "Druck-PDF heruntergeladen");
    });

  const handleShare = () =>
    run("share", async () => {
      const blob = await exportPromo(sessionId, format);
      const file = new File([blob], `${base}_${format}.png`, { type: "image/png" });
      try {
        await navigator.share({ files: [file], title: productName || "EDEKA Promotion" });
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return; // Nutzer hat abgebrochen
        throw err;
      }
    });

  const spinner = (text: string) => (
    <span className="flex items-center gap-2">
      <span className="spinner" />
      {text}
    </span>
  );

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
      <button type="button" onClick={handleZip} disabled={busy !== ""} className="btn-ghost sm:w-auto">
        {busy === "zip" ? spinner("ZIP wird erstellt") : "Alle Formate (ZIP)"}
      </button>
      <button type="button" onClick={handlePdf} disabled={busy !== ""} className="btn-ghost sm:w-auto">
        {busy === "pdf" ? spinner("PDF wird erstellt") : "Druck-PDF"}
      </button>
      {canShare && (
        <button type="button" onClick={handleShare} disabled={busy !== ""} className="btn-ghost sm:w-auto">
          {busy === "share" ? spinner("Wird geteilt") : "Teilen"}
        </button>
      )}
      <button type="button" onClick={handleDownload} disabled={busy !== ""} className="btn-primary sm:w-auto">
        {busy === "png" ? (
          spinner("Wird heruntergeladen")
        ) : (
          <span className="flex items-center gap-2">
            <DownloadIcon />
            Als {label} herunterladen
          </span>
        )}
      </button>
    </div>
  );
}
