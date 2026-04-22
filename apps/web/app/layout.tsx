import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Product Radar",
  description: "Official AI product release tracking and review system"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
