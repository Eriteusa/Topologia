import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SoftCast",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
