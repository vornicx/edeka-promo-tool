import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EDEKA Mühlenbein - Promo Tool",
  description: "Promotionen mit KI und lokalem Profi-Modus erstellen",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}
