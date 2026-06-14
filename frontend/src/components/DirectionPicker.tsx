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
    <div className="card">
      <h2 className="text-2xl font-bold text-edeka-blue mb-4">
        Elige una dirección creativa
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {directions.map((dir, i) => (
          <button
            key={dir.name}
            onClick={() => onSelect(i)}
            className={`p-4 rounded-xl border-2 text-left transition-all duration-200 ${
              selectedIndex === i
                ? "border-edeka-blue bg-blue-50 shadow-lg"
                : "border-gray-200 hover:border-gray-400"
            }`}
          >
            <div className="flex gap-1 mb-2">
              {dir.palette.map((color, ci) => (
                <div
                  key={ci}
                  className="w-6 h-6 rounded-full border border-gray-300"
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <h3 className="font-bold text-lg capitalize">{dir.name.replace(/_/g, " ")}</h3>
            <p className="text-sm text-gray-600 mt-1">{dir.intent}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
              <span className="bg-gray-100 px-2 py-1 rounded">{dir.boldness}</span>
              <span className="bg-gray-100 px-2 py-1 rounded">{dir.text_safe_area}</span>
              {dir.waschbaer_presence !== "none" && (
                <span className="bg-edeka-yellow/20 px-2 py-1 rounded">🦝</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
