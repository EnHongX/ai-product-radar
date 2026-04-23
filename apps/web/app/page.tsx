import { HomeContent } from "@/components/home-content";

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

async function getStats(): Promise<StatsData> {
  const apiBaseUrl = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  try {
    const response = await fetch(`${apiBaseUrl}/api/stats`, { cache: "no-store" });

    if (!response.ok) {
      return { companies: 0, sources: 0, products: 0 };
    }

    return response.json();
  } catch {
    return { companies: 0, sources: 0, products: 0 };
  }
}

export default async function Home() {
  const [health, stats] = await Promise.all([getHealth(), getStats()]);

  return <HomeContent health={health} stats={stats} />;
}
