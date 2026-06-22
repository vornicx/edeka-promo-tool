"use client";

import { CreativeDirection } from "@/lib/api";

interface Props {
  directions: CreativeDirection[];
  selectedIndex: number | null;
  onSelect: (index: number) => void;
}

function getBoldnessLabel(value: string) {
  if (value === "high") return "Mutig";
  if (value === "medium") return "Ausgewogen";
  return "Dezent";
}

export default function DirectionPicker({ directions, selectedIndex, onSelect }: Props) {
  if (!directions.length) return null;

  return (
    <div className="panel overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-slate-200 bg-white p-5 sm:p-6 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-edeka-blue">Kreativrichtungen</p>
          <h2 className="mt-2 text-2xl font-extrabold text-slate-950">Visuellen Ansatz wählen</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
            Vergleiche Wirkung, Komposition und Farben, bevor die finale Promotion erstellt wird.
          </p>
        </div>
        <span className="rounded-lg bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600">
          {selectedIndex === null ? "Keine Auswahl" : `Option ${selectedIndex + 1} gewählt`}
        </span>
      </div>

      <div className="grid gap-3 p-5 sm:p-6 lg:grid-cols-3">
        {directions.map((dir, index) => {
          const selected = selectedIndex === index;
          return (
            <button
              key={`${dir.name}-${index}`}
              type="button"
              onClick={() => onSelect(index)}
              aria-pressed={selected}
              className={`group flex min-h-[260px] flex-col rounded-lg border p-4 text-left transition-all ${
                selected
                  ? "border-edeka-blue bg-edeka-lightblue shadow-elevated"
                  : "border-slate-200 bg-white hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-card"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className={`badge ${selected ? "bg-white text-edeka-blue" : "bg-slate-100 text-slate-600"}`}>
                    Option {index + 1}
                  </span>
                  <h3 className="mt-3 text-lg font-extrabold capitalize leading-tight text-slate-950">
                    {dir.name.replace(/_/g, " ")}
                  </h3>
                </div>
                <span
                  className={`grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-extrabold ${
                    selected ? "border-edeka-blue bg-edeka-blue text-white" : "border-slate-200 bg-white text-slate-300"
                  }`}
                >
                  {selected && (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-5 gap-1.5">
                {dir.palette.slice(0, 5).map((color, colorIndex) => (
                  <span
                    key={`${color}-${colorIndex}`}
                    className="h-8 rounded-md border border-white shadow-sm"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>

              <p className="mt-4 text-sm leading-6 text-slate-600">{dir.intent}</p>

              <div className="mt-4 rounded-lg bg-slate-50 p-3">
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Komposition</p>
                <p className="mt-1 line-clamp-3 text-sm leading-6 text-slate-600">{dir.composition}</p>
              </div>

              <div className="mt-auto flex flex-wrap gap-2 pt-4">
                <span
                  className={`badge ${
                    dir.boldness === "high"
                      ? "bg-orange-50 text-orange-700"
                      : dir.boldness === "medium"
                        ? "bg-blue-50 text-blue-700"
                        : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {getBoldnessLabel(dir.boldness)}
                </span>
                {dir.waschbaer_presence !== "none" && (
                  <span className="badge bg-edeka-yellow/25 text-edeka-blue">Waschbär</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
