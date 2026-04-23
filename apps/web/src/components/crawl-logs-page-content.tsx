"use client";

import { useEffect, useState } from "react";
import { Eye, X, CheckCircle, XCircle, Loader2 } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { useLanguage } from "@/i18n";
import type { CrawlLog, Company, Source } from "@/lib/api";
import { fetchCrawlLogs, fetchCompanies, fetchSources } from "@/lib/api";

export function CrawlLogsPageContent() {
  const { t } = useLanguage();
  const [logs, setLogs] = useState<CrawlLog[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [filterCompanyId, setFilterCompanyId] = useState<number | undefined>(undefined);
  const [filterSourceId, setFilterSourceId] = useState<number | undefined>(undefined);
  const [filterStatus, setFilterStatus] = useState<string | undefined>(undefined);
  
  const [selectedLog, setSelectedLog] = useState<CrawlLog | null>(null);
  const [showErrorModal, setShowErrorModal] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [companiesData, sourcesData] = await Promise.all([
        fetchCompanies(),
        fetchSources(),
      ]);
      setCompanies(companiesData);
      setSources(sourcesData);
      
      const logsData = await fetchCrawlLogs(filterSourceId, filterCompanyId, filterStatus, 50, 0);
      setLogs(logsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load crawl logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterCompanyId, filterSourceId, filterStatus]);

  const handleViewError = (log: CrawlLog) => {
    setSelectedLog(log);
    setShowErrorModal(true);
  };

  const handleCloseError = () => {
    setShowErrorModal(false);
    setSelectedLog(null);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "success":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            {getStatusIcon(status)}
            {t.crawlLogs.success}
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            {getStatusIcon(status)}
            {t.crawlLogs.failed}
          </span>
        );
      case "running":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {getStatusIcon(status)}
            {t.crawlLogs.running}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            {status}
          </span>
        );
    }
  };

  const getCompanyName = (log: CrawlLog) => {
    if (log.company?.name) return log.company.name;
    return "-";
  };

  const getSourceName = (log: CrawlLog) => {
    if (log.source?.name) return log.source.name;
    const source = sources.find(s => s.id === log.source_id);
    return source?.name || "-";
  };

  const filteredSources = filterCompanyId
    ? sources.filter(s => s.company_id === filterCompanyId)
    : sources;

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{t.crawlLogs.title}</h2>
        </div>

        <div className="flex flex-wrap items-center gap-4 px-5 py-3 border-b border-line bg-gray-50">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.crawlLogs.filterByStatus}:</label>
            <select
              value={filterStatus === undefined ? "" : filterStatus}
              onChange={(e) => setFilterStatus(e.target.value === "" ? undefined : e.target.value)}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.crawlLogs.allStatus}</option>
              <option value="success">{t.crawlLogs.success}</option>
              <option value="failed">{t.crawlLogs.failed}</option>
              <option value="running">{t.crawlLogs.running}</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.crawlLogs.filterByCompany}:</label>
            <select
              value={filterCompanyId === undefined ? "" : filterCompanyId}
              onChange={(e) => {
                setFilterCompanyId(e.target.value === "" ? undefined : parseInt(e.target.value));
                setFilterSourceId(undefined);
              }}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.crawlLogs.allCompanies}</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.crawlLogs.filterBySource}:</label>
            <select
              value={filterSourceId === undefined ? "" : filterSourceId}
              onChange={(e) => setFilterSourceId(e.target.value === "" ? undefined : parseInt(e.target.value))}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.crawlLogs.allSources}</option>
              {filteredSources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="mx-5 mt-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {loading ? (
          <div className="px-5 py-8 text-center text-muted">{t.common.loading}</div>
        ) : logs.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <p className="text-muted">{t.crawlLogs.noLogs}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.crawlLogs.status}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden md:table-cell">{t.crawlLogs.company}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.crawlLogs.source}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden sm:table-cell">{t.crawlLogs.articlesFound}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden sm:table-cell">{t.crawlLogs.articlesCreated}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">{t.crawlLogs.startedAt}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">{t.crawlLogs.finishedAt}</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-ink">{t.crawlLogs.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      {getStatusBadge(log.status)}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-sm text-muted">{getCompanyName(log)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-ink">{getSourceName(log)}</span>
                        <span className="text-xs text-muted md:hidden">
                          {getCompanyName(log)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span className="text-sm text-ink font-medium">{log.articles_found}</span>
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span className="text-sm text-ink font-medium">{log.articles_created}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <span className="text-sm text-muted">{formatDate(log.started_at)}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <span className="text-sm text-muted">{formatDate(log.finished_at)}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {log.status === "failed" && log.error_message && (
                        <button
                          onClick={() => handleViewError(log)}
                          className="rounded p-1.5 text-muted hover:text-red-600 hover:bg-red-50 transition-colors"
                          title={t.crawlLogs.viewError}
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showErrorModal && selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <h3 className="text-base font-semibold text-ink">{t.crawlLogs.errorDetail}</h3>
              <button
                onClick={handleCloseError}
                className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.source}</label>
                    <p className="text-ink mt-1">{getSourceName(selectedLog)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.status}</label>
                    <p className="mt-1">{getStatusBadge(selectedLog.status)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.articlesFound}</label>
                    <p className="text-ink mt-1">{selectedLog.articles_found}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.articlesCreated}</label>
                    <p className="text-ink mt-1">{selectedLog.articles_created}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.startedAt}</label>
                    <p className="text-ink mt-1">{formatDate(selectedLog.started_at)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.finishedAt}</label>
                    <p className="text-ink mt-1">{formatDate(selectedLog.finished_at)}</p>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-muted">{t.crawlLogs.errorMessage}</label>
                  <div className="mt-1 p-4 bg-red-50 rounded-md border border-red-200 max-h-[400px] overflow-y-auto">
                    <pre className="text-sm text-red-800 whitespace-pre-wrap break-words">
                      {selectedLog.error_message}
                    </pre>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end border-t border-line px-5 py-4">
              <button
                onClick={handleCloseError}
                className="inline-flex items-center gap-2 rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-200 transition-colors"
              >
                {t.crawlLogs.close}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
