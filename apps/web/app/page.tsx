import { Activity, Database, Layers3, Server } from "lucide-react";

import { StatusPill } from "@/components/status-pill";

type HealthResponse = {
  status: "ok" | "degraded";
  environment: string;
  services: Record<string, string>;
  errors: Record<string, string>;
};

async function getHealth(): Promise<HealthResponse | null> {
  const apiBaseUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  try {
    const response = await fetch(`${apiBaseUrl}/health`, { cache: "no-store" });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

const phaseItems = [
  { label: "Phase 1", value: "Foundation", status: "completed" },
  { label: "Phase 2", value: "Database schema", status: "completed" },
  { label: "Phase 3", value: "Companies admin", status: "pending" },
  { label: "Phase 4", value: "Sources admin", status: "pending" }
];

export default async function Home() {
  const health = await getHealth();
  const services = health?.services ?? { api: "unknown", database: "unknown", redis: "unknown" };

  return (
    <main className="min-h-screen">
      <section className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-8 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">Official release intelligence</p>
            <h1 className="mt-3 text-3xl font-semibold text-ink md:text-5xl">AI Product Radar</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
              Backend-first system for collecting official AI product releases, preserving source traceability, and
              reviewing structured records before publication.
            </p>
          </div>
          <StatusPill status={health?.status ?? "degraded"} label={health?.status ?? "offline"} />
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 py-8 md:grid-cols-3">
        <div className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <Server className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">API</h2>
          </div>
          <p className="mt-4 text-2xl font-semibold">{services.api}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <Database className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">Database</h2>
          </div>
          <p className="mt-4 text-2xl font-semibold">{services.database}</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">Redis</h2>
          </div>
          <p className="mt-4 text-2xl font-semibold">{services.redis}</p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-10">
        <div className="rounded-lg border border-line bg-white">
          <div className="flex items-center gap-3 border-b border-line px-5 py-4">
            <Layers3 className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 className="text-base font-semibold">Development Phases</h2>
          </div>
          <div className="divide-y divide-line">
            {phaseItems.map((item) => (
              <div key={item.label} className="grid gap-2 px-5 py-4 md:grid-cols-[120px_1fr_120px] md:items-center">
                <span className="font-medium text-ink">{item.label}</span>
                <span className="text-muted">{item.value}</span>
                <StatusPill status={item.status === "completed" ? "ok" : "degraded"} label={item.status} />
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
