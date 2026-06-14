"use client";

import { useState } from "react";
import { getImageUrl } from "@/lib/api";

interface Props {
  sessionId: string | null;
  composed: boolean;
}

export default function PreviewPanel({ sessionId, composed }: Props) {
  const [imgError, setImgError] = useState(false);

  if (!sessionId) return null;

  const imageUrl = getImageUrl(sessionId);

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-edeka-blue mb-4">Preview</h2>
      {composed ? (
        <div className="flex justify-center">
          {imgError ? (
            <div className="flex items-center justify-center h-64 bg-red-50 rounded-lg">
              <p className="text-red-600">Error al cargar la imagen. Inténtalo de nuevo.</p>
            </div>
          ) : (
            <img
              src={imageUrl}
              alt="Preview de promoción"
              className="max-w-full max-h-[600px] rounded-lg shadow-lg"
              onError={() => setImgError(true)}
            />
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
          <p className="text-gray-500">
            Selecciona una dirección y haz clic en &quot;Componer&quot; para ver la preview
          </p>
        </div>
      )}
    </div>
  );
}
