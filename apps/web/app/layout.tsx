"use client";

import { LanguageProvider } from "@/i18n";
import "./globals.css";

export const metadata = {
  title: "AI Product Radar",
  description: "Official AI product release tracking and review system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
