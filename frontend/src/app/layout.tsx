import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EDEKA Mühlenbein - Promo Tool",
  description: "Herramienta de creación de promociones con IA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
