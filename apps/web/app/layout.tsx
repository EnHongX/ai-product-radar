import type { Metadata } from "next";
import { ClientProvider } from "@/components/client-provider";
import "./globals.css";

export const metadata: Metadata = {
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
        <ClientProvider>{children}</ClientProvider>
      </body>
    </html>
  );
}
