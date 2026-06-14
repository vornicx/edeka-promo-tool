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

  const imageUrl = getImageUrl(sessionId);

  return (
    <>
      <div className="card">
        <div className="flex items-center gap-3 pb-2 border-b-2 border-edeka-blue/10 mb-5">
          <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-edeka-blue">Previsualización</h2>
            <p className="text-sm text-gray-500">
              {composed ? "Resultado final de la promoción" : "Completa los pasos anteriores para ver el resultado"}
            </p>
          </div>
        </div>

        {composed ? (
          <div className="flex justify-center">
            {imgError ? (
              <div className="flex flex-col items-center justify-center h-64 bg-red-50 rounded-2xl border-2 border-red-200 p-6">
                <svg className="w-10 h-10 text-red-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <p className="text-red-600 font-medium">Error al cargar la imagen</p>
                <p className="text-red-400 text-sm mt-1">Intenta componer de nuevo</p>
              </div>
            ) : (
              <div className="relative group">
                <img
                  src={imageUrl}
                  alt="Preview de promoción"
                  className="max-w-full max-h-[500px] rounded-2xl shadow-lg cursor-pointer
                    transition-transform duration-300 group-hover:scale-[1.01]"
                  onClick={() => setLightbox(true)}
                  onError={() => setImgError(true)}
                />
                <div className="absolute inset-0 rounded-2xl bg-black/0 group-hover:bg-black/10 transition-colors duration-300 flex items-center justify-center">
                  <span className="text-white text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity bg-black/50 px-4 py-2 rounded-xl">
                    Clic para ampliar
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl border-2 border-dashed border-gray-300">
            <svg className="w-12 h-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-gray-400 font-medium">Selecciona una dirección y compón</p>
            <p className="text-gray-300 text-sm mt-1">Aquí verás el resultado visual</p>
          </div>
        )}
      </div>

      {lightbox && composed && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in"
          onClick={() => setLightbox(false)}
        >
          <button
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/20 text-white flex items-center justify-center hover:bg-white/30 transition-colors"
            onClick={() => setLightbox(false)}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <img
            src={imageUrl}
            alt="Preview ampliada"
            className="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-2xl animate-bounce-in"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}
