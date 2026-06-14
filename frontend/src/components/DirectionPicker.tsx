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
      <h2 className="section-title mb-4">Direcciones creativas</h2>
      <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
        {directions.map((dir, i) => (
          <button
            key={dir.name}
            onClick={() => onSelect(i)}
            className={`flex-shrink-0 w-64 p-4 rounded-xl border-2 text-left transition-all ${
              selectedIndex === i
                ? "border-edeka-blue/30 bg-edeka-blue/[0.03] shadow-sm"
                : "border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50/50"
            }`}
          >
            <div className="flex gap-1 mb-3">
              {dir.palette.slice(0, 5).map((c, ci) => (
                <div key={ci} className="w-5 h-5 rounded-md border border-white/50 shadow-sm"
                  style={{ backgroundColor: c }} />
              ))}
            </div>
            <h3 className="text-sm font-bold text-gray-900 capitalize mb-1">
              {dir.name.replace(/_/g, " ")}
            </h3>
            <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">
              {dir.intent}
            </p>
            <div className="flex gap-2 mt-3">
              <span className={`badge ${
                dir.boldness === "high" ? "bg-orange-50 text-orange-600" :
                dir.boldness === "medium" ? "bg-blue-50 text-blue-600" :
                "bg-gray-50 text-gray-500"
              }`}>
                {dir.boldness === "high" ? "Arriesgado" : dir.boldness === "medium" ? "Moderado" : "Sutil"}
              </span>
              {dir.waschbaer_presence !== "none" && (
                <span className="badge bg-edeka-yellow/10 text-edeka-blue">Waschbär</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
