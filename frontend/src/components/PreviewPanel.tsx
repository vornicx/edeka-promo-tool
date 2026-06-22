"use client";

import { useEffect, useState } from "react";
import { getImageUrl } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
  version?: number;
}

export default function PreviewPanel({ sessionId, composed, version = 0 }: Props) {
  const [imgError, setImgError] = useState(false);
  const [lightbox, setLightbox] = useState(false);

  // Reset the error state whenever a new composition is rendered.
  useEffect(() => {
    setImgError(false);
  }, [version, sessionId]);

  if (!sessionId) return null;

  const imageSrc = `${getImageUrl(sessionId)}?v=${version}`;

  return (
    <>
      <div className="panel overflow-hidden">
        <div className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white p-5 sm:p-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Vorschau</p>
            <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Erstellte Promotion</h2>
          </div>
          <span className="rounded-lg bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700">Bereit</span>
        </div>

        <div className="bg-preview-grid p-4 sm:p-8">
          {composed ? (
            <div className="flex justify-center">
              {imgError ? (
                <div className="grid min-h-[420px] w-full place-items-center rounded-lg border border-dashed border-slate-300 bg-white text-center">
                  <div>
                    <svg className="mx-auto h-9 w-9 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M12 9v3m0 4h.01M10.3 4.3L2.8 17.5A2 2 0 004.5 20h15a2 2 0 001.7-2.5L13.7 4.3a2 2 0 00-3.4 0z" />
                    </svg>
                    <p className="mt-3 text-sm font-semibold text-slate-700">Bild konnte nicht geladen werden</p>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setLightbox(true)}
                  className="group relative max-w-full rounded-lg bg-white p-3 shadow-elevated outline-none transition-transform hover:-translate-y-0.5 focus:ring-4 focus:ring-edeka-blue/15"
                >
                  <img
                    src={imageSrc}
                    alt="Vorschau der Promotion"
                    className="max-h-[620px] max-w-full rounded-md border border-slate-200 object-contain"
                    onError={() => setImgError(true)}
                  />
                  <span className="absolute bottom-5 left-1/2 -translate-x-1/2 rounded-lg border border-white/70 bg-slate-950/75 px-3 py-2 text-xs font-bold text-white opacity-0 shadow-sm backdrop-blur transition-opacity group-hover:opacity-100 group-focus:opacity-100">
                    Vorschau vergrößern
                  </span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid min-h-[420px] place-items-center rounded-lg border border-dashed border-slate-300 bg-white/80 text-center">
              <div>
                <svg className="mx-auto h-10 w-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M4 16l4-4a2 2 0 012.8 0L16 17m-2-2l1.2-1.2a2 2 0 012.8 0L20 16M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="mt-3 text-sm font-semibold text-slate-500">Die Vorschau erscheint hier</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {lightbox && composed && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
          onClick={() => setLightbox(false)}
        >
          <button
            type="button"
            className="absolute right-4 top-4 rounded-lg bg-white/10 px-3 py-2 text-sm font-bold text-white backdrop-blur transition-colors hover:bg-white/20"
            onClick={() => setLightbox(false)}
          >
            Schließen
          </button>
          <img
            src={imageSrc}
            alt="Vergrößerte Vorschau"
            className="max-h-[90vh] max-w-[92vw] rounded-lg bg-white shadow-modal animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}
