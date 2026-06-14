"use client";

import { useEffect, useState } from "react";

const C = ["#FFD600", "#FF6B6B", "#4ECDC4", "#45B7D1"];

interface P { id: number; x: number; c: string; s: number; d: number; }

interface Props { active: boolean; }

export default function Confetti({ active }: Props) {
  const [p, setP] = useState<P[]>([]);
  useEffect(() => {
    if (!active) { setP([]); return; }
    const a: P[] = Array.from({ length: 24 }, (_, i) => ({
      id: i, x: Math.random() * 100, c: C[Math.floor(Math.random() * C.length)],
      s: 4 + Math.random() * 5, d: 1 + Math.random() * 0.8,
    }));
    setP(a);
    const t = setTimeout(() => setP([]), 2200);
    return () => clearTimeout(t);
  }, [active]);

  if (!p.length) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-[60] overflow-hidden">
      {p.map((x) => (
        <div key={x.id} className="absolute top-0 animate-confetti-fall rounded-sm"
          style={{ left: `${x.x}%`, width: x.s, height: x.s, backgroundColor: x.c,
            animationDelay: `${Math.random() * 0.2}s`, animationDuration: `${x.d}s` }} />
      ))}
    </div>
  );
}
