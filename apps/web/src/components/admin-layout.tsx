"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, Database, Tags, Layers, FileText, History } from "lucide-react";

import { Header } from "@/components/header";
import { useLanguage } from "@/i18n";

interface AdminLayoutProps {
  children: React.ReactNode;
}

export function AdminLayout({ children }: AdminLayoutProps) {
  const { t } = useLanguage();
  const pathname = usePathname();

  const navItems = [
    {
      href: "/admin/companies",
      label: t.admin.companies,
      icon: Building2,
      active: pathname === "/admin" || pathname === "/admin/companies",
    },
    {
      href: "/admin/company-types",
      label: t.admin.companyTypes,
      icon: Tags,
      active: pathname === "/admin/company-types",
    },
    {
      href: "/admin/sources",
      label: t.admin.sources,
      icon: Database,
      active: pathname === "/admin/sources",
    },
    {
      href: "/admin/source-types",
      label: t.admin.sourceTypes,
      icon: Layers,
      active: pathname === "/admin/source-types",
    },
    {
      href: "/admin/raw-articles",
      label: t.admin.rawArticles,
      icon: FileText,
      active: pathname === "/admin/raw-articles",
    },
    {
      href: "/admin/crawl-logs",
      label: t.admin.crawlLogs,
      icon: History,
      active: pathname === "/admin/crawl-logs",
    },
  ];

  return (
    <main className="min-h-screen">
      <Header />

      <div className="mx-auto flex max-w-7xl gap-6 px-6 py-8">
        <aside className="w-48 shrink-0">
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    item.active
                      ? "bg-accent/10 text-accent"
                      : "text-muted hover:bg-gray-100 hover:text-ink"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="flex-1">{children}</div>
      </div>
    </main>
  );
}
