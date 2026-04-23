"use client";

import { Activity, Database, Server } from "lucide-react";

import { Header } from "@/components/header";
import { StatisticsCards } from "@/components/statistics-cards";
import { StatusPill } from "@/components/status-pill";
import { useLanguage } from "@/i18n";

type HealthResponse = {
  status: "ok" | "degraded";
  environment: string;
  services: Record<string, string>;
  errors: Record<string, string>;
};

type StatsData = {
  companies: number;
  sources: number;
  products: number;
};

type HomeContentProps = {
  health: HealthResponse | null;
  stats: StatsData;
};

export function HomeContent({ health, stats }: HomeContentProps) {
  const { t } = useLanguage();
  const services = health?.services ?? { api: "unknown", database: "unknown", redis: "unknown" };

  return (
    <main className="min-h-screen">
      <Header />

      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">
              {t.homepage.subtitle}
            </p>
            <h1 className="mt-3 text-3xl font-semibold text-ink md:text-5xl">{t.homepage.title}</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted">{t.homepage.description}</p>
          </div>
          <StatusPill status={health?.status ?? "degraded"} label={health?.status ?? "offline"} />
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 py-8 md:grid-cols-3">
        <div className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <Server className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">{t.homepage.api}</h2>
          </div>
          <p className="mt-4 text-2xl font-semibold">{services.api}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">{t.homepage.database}</h2>
          </div>
          <p className="mt-4 text-2xl font-semibold">{services.database}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">{t.homepage.redis}</h2>
          </div>
          <p className="mt-4 text-2xl font-semibold">{services.redis}</p>
        </div>
      </section>

      <StatisticsCards stats={stats} />
    </main>
  );
}
