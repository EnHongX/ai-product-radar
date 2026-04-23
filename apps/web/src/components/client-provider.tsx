"use client";

import { LanguageProvider } from "@/i18n";

interface ClientProviderProps {
  children: React.ReactNode;
}

export function ClientProvider({ children }: ClientProviderProps) {
  return <LanguageProvider>{children}</LanguageProvider>;
}
