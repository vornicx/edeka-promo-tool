"use client";

import { CreativeDirection } from "@/lib/api";

interface Props {
  directions: CreativeDirection[];
  selectedIndex: number | null;
  onSelect: (index: number) => void;
}

export default function DirectionPicker({ directions, selectedIndex, onSelect }: Props) {
  if (!directions.length) return null;

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">🎨</span>
        <h2 className="text-sm font-bold text-gray-700">Elige una dirección</h2>
        <span className="text-xs text-gray-400">({directions.length})</span>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {directions.map((dir, i) => (
          <button
            key={dir.name}
            onClick={() => onSelect(i)}
            className={`flex-shrink-0 w-56 p-3 rounded-xl border-2 text-left transition-all ${
              selectedIndex === i
                ? "border-edeka-blue bg-edeka-lightblue/50 shadow-sm"
                : "border-gray-100 bg-gray-50/50 hover:border-gray-200 hover:bg-white"
            }`}
          >
            <div className="flex gap-1 mb-2">
              {dir.palette.slice(0, 4).map((c, ci) => (
                <div key={ci} className="w-4 h-4 rounded border border-white/50" style={{ backgroundColor: c }} />
              ))}
            </div>
            <h3 className="text-sm font-bold text-gray-800 capitalize leading-tight">
              {dir.name.replace(/_/g, " ")}
            </h3>
            <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
              {dir.intent}
            </p>
            <div className="flex gap-1 mt-2">
              <span className="badge bg-gray-100 text-gray-500">
                {dir.boldness === "high" ? "🔥" : dir.boldness === "medium" ? "⚡" : "🌱"}
              </span>
              {dir.waschbaer_presence !== "none" && (
                <span className="badge bg-edeka-yellow/10 text-edeka-blue">🦝</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
