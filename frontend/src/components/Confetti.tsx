"use client";

import { useEffect, useState } from "react";

const COLORS = ["#FFD600", "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"];

interface Piece { id: number; x: number; color: string; size: number; delay: number; duration: number; }

interface Props { active: boolean; }

export default function Confetti({ active }: Props) {
  const [pieces, setPieces] = useState<Piece[]>([]);

  useEffect(() => {
    if (!active) { setPieces([]); return; }
    const g: Piece[] = Array.from({ length: 30 }, (_, i) => ({
      id: i, x: Math.random() * 100,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      size: 4 + Math.random() * 6, delay: Math.random() * 0.3, duration: 1.5 + Math.random() * 1,
    }));
    setPieces(g);
    const t = setTimeout(() => setPieces([]), 3000);
    return () => clearTimeout(t);
  }, [active]);

  if (!pieces.length) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-[60] overflow-hidden">
      {pieces.map((p) => (
        <div
          key={p.id}
          className="absolute top-0 animate-confetti-fall rounded-sm"
          style={{
            left: `${p.x}%`, width: p.size, height: p.size,
            backgroundColor: p.color, animationDelay: `${p.delay}s`, animationDuration: `${p.duration}s`,
          }}
        />
      ))}
    </div>
  );
}
