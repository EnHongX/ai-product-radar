"use client";

import { Building2, Database, Package } from "lucide-react";
import { useLanguage } from "@/i18n";

type StatsData = {
  companies: number;
  sources: number;
  products: number;
};

type StatisticsCardsProps = {
  stats: StatsData;
};

export function StatisticsCards({ stats }: StatisticsCardsProps) {
  const { t } = useLanguage();

  const items = [
    {
      icon: Building2,
      label: t.common.companies,
      value: stats.companies,
    },
    {
      icon: Database,
      label: t.common.sources,
      value: stats.sources,
    },
    {
      icon: Package,
      label: t.common.products,
      value: stats.products,
    },
  ];

  return (
    <section className="mx-auto grid max-w-7xl gap-4 px-6 py-8 md:grid-cols-3">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className="rounded-lg border border-line bg-white p-5">
            <div className="flex items-center gap-3">
              <Icon className="h-5 w-5 text-accent" aria-hidden="true" />
              <h2 className="text-base font-semibold">{item.label}</h2>
            </div>
            <p className="mt-4 text-2xl font-semibold">{item.value}</p>
          </div>
        );
      })}
    </section>
  );
}
