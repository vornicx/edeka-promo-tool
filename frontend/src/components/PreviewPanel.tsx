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
        <h2 className="section-title mb-4">Vista previa</h2>
        {composed ? (
          <div className="flex justify-center">
            {imgError ? (
              <div className="flex flex-col items-center py-12 text-gray-400">
                <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm">Error al cargar la imagen</p>
              </div>
            ) : (
              <div className="relative group cursor-pointer" onClick={() => setLightbox(true)}>
                <img src={getImageUrl(sessionId)} alt="Preview"
                  className="max-h-[420px] rounded-xl border border-gray-100 shadow-sm
                    transition-all duration-200 group-hover:shadow-md"
                  onError={() => setImgError(true)} />
                <div className="absolute inset-0 rounded-xl bg-black/0 group-hover:bg-black/[0.02] transition-colors flex items-center justify-center">
                  <span className="text-xs text-white/0 group-hover:text-gray-500 transition-colors
                    bg-white/80 backdrop-blur-sm px-3 py-1.5 rounded-lg shadow-sm border border-gray-100">
                    Ampliar
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center py-12 text-gray-300">
            <svg className="w-10 h-10 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-sm font-medium text-gray-400">Completa los pasos anteriores</p>
          </div>
        )}
      </div>

      {lightbox && composed && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setLightbox(false)}>
          <img src={getImageUrl(sessionId)} alt="Preview"
            className="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-modal animate-scale-in"
            onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </>
  );
}
