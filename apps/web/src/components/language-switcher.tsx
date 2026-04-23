"use client";

import { Globe } from "lucide-react";

import { useLanguage, type Locale } from "@/i18n";

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useLanguage();

  const handleChange = (newLocale: Locale) => {
    setLocale(newLocale);
  };

  return (
    <div className="flex items-center gap-2">
      <Globe className="h-4 w-4 text-accent" />
      <select
        value={locale}
        onChange={(e) => handleChange(e.target.value as Locale)}
        className="text-sm border border-line rounded px-2 py-1 bg-white text-ink focus:outline-none focus:ring-2 focus:ring-accent"
      >
        <option value="en">EN</option>
        <option value="zh">中文</option>
      </select>
    </div>
  );
}
