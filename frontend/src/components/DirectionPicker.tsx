"use client";

import { CreativeDirection } from "@/lib/api";

interface Props {
  directions: CreativeDirection[];
  selectedIndex: number | null;
  onSelect: (index: number) => void;
}

export default function DirectionPicker({
  directions,
  selectedIndex,
  onSelect,
}: Props) {
  if (directions.length === 0) return null;

  return (
    <div className="glass-card-strong">
      <div className="flex items-center gap-3 pb-2 border-b border-white/40 mb-5">
        <div className="w-10 h-10 rounded-xl bg-edeka-yellow/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-edeka-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-extrabold text-edeka-blue">
            Elige una dirección creativa
          </h2>
          <p className="text-sm text-gray-500">
            La IA ha generado {directions.length} propuestas distintas
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {directions.map((dir, i) => (
          <button
            key={dir.name}
            onClick={() => onSelect(i)}
            className={`relative p-5 rounded-2xl border-2 text-left transition-all duration-300 ${
              selectedIndex === i
                ? "border-edeka-blue/50 bg-edeka-lightblue/60 backdrop-blur-sm shadow-elevated scale-[1.02]"
                : "border-white/40 bg-white/30 backdrop-blur-sm hover:bg-white/50 hover:border-edeka-blue/30 hover:shadow-glass-blue hover:-translate-y-0.5"
            }`}
          >
            {selectedIndex === i && (
              <div className="absolute -top-2.5 -right-2.5 w-7 h-7 rounded-full bg-edeka-blue text-white flex items-center justify-center shadow-md">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            )}

            <div className="flex gap-1.5 mb-3">
              {dir.palette.map((color, ci) => (
                <div
                  key={ci}
                  className="w-7 h-7 rounded-lg border border-gray-200 shadow-sm transition-transform hover:scale-110"
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>

            <h3 className="font-extrabold text-base capitalize text-gray-800 mb-1">
              {dir.name.replace(/_/g, " ")}
            </h3>
            <p className="text-sm text-gray-600 leading-relaxed line-clamp-3">
              {dir.intent}
            </p>

            <div className="mt-3 flex flex-wrap gap-1.5">
              <span className="badge-glass text-gray-600">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                {dir.boldness === "high" ? "Arriesgado" : dir.boldness === "medium" ? "Moderado" : "Sutil"}
              </span>
              {dir.waschbaer_presence !== "none" && (
                <span className="badge-glass bg-edeka-yellow/20 text-edeka-darkblue border-edeka-yellow/30">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                  </svg>
                  Waschbär
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
