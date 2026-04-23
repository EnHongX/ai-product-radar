"use client";

import { AdminLayout } from "@/components/admin-layout";
import { useLanguage } from "@/i18n";

export default function SourcesPage() {
  const { t } = useLanguage();

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white p-8">
        <h2 className="text-lg font-semibold text-ink mb-4">{t.admin.sourceManagement}</h2>
        <p className="text-muted">{t.common.noData}</p>
      </div>
    </AdminLayout>
  );
}
