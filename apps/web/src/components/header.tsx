"use client";

import Link from "next/link";

import { LanguageSwitcher } from "@/components/language-switcher";
import { useLanguage } from "@/i18n";

export function Header() {
  const { t } = useLanguage();

  return (
    <header className="border-b border-line bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold text-ink">
          AI Product Radar
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href="/admin"
            className="text-sm font-medium text-accent hover:text-accent/80 transition-colors"
          >
            {t.homepage.adminLink}
          </Link>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
