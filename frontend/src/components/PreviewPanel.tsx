"use client";

import { useState } from "react";
import { getImageUrl } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

export default function PreviewPanel({ sessionId, composed }: Props) {
  const [imgError, setImgError] = useState(false);
  const [lightbox, setLightbox] = useState(false);

  if (!sessionId) return null;

  return (
    <>
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">👁</span>
          <h2 className="text-sm font-bold text-gray-700">Previsualización</h2>
        </div>

        {composed ? (
          <div className="flex justify-center">
            {imgError ? (
              <div className="flex flex-col items-center py-10 text-red-500">
                <span className="text-2xl mb-1">⚠</span>
                <p className="text-sm font-medium">Error al cargar la imagen</p>
              </div>
            ) : (
              <div className="relative group cursor-pointer" onClick={() => setLightbox(true)}>
                <img
                  src={getImageUrl(sessionId)}
                  alt="Preview"
                  className="max-h-[400px] rounded-lg shadow-sm border border-gray-100"
                  onError={() => setImgError(true)}
                />
                <div className="absolute inset-0 rounded-lg bg-black/0 group-hover:bg-black/5 transition-colors flex items-center justify-center">
                  <span className="text-xs text-white/0 group-hover:text-white/70 transition-colors bg-black/40 px-3 py-1 rounded-md">
                    Ampliar
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center py-10 text-gray-300">
            <span className="text-3xl mb-2">🖼</span>
            <p className="text-sm font-medium text-gray-400">Completa los pasos anteriores</p>
          </div>
        )}
      </div>

      {lightbox && composed && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
          onClick={() => setLightbox(false)}
        >
          <img
            src={getImageUrl(sessionId)}
            alt="Preview"
            className="max-w-[90vw] max-h-[90vh] rounded-xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}
