"use client";

import { useEffect, useState } from "react";
import { Eye, X, CheckCircle, XCircle, Loader2, AlertTriangle, Info, ChevronDown, ChevronRight } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { useLanguage } from "@/i18n";
import type { CrawlLog, Company, Source } from "@/lib/api";
import { fetchCrawlLogs, fetchCompanies, fetchSources } from "@/lib/api";

interface LogBreakdown {
  total_articles_found?: number;
  successfully_created?: number;
  skipped_reasons?: {
    url_already_exists?: number;
    content_hash_already_exists?: number;
    total_skipped?: number;
  };
  failed_reasons?: {
    parse_failed?: number;
    database_operation_failed?: number;
    total_failed?: number;
  };
  summary?: string;
}

interface ArticleRecord {
  index: number;
  title: string;
  url: string;
  status: string;
  error_message?: string;
  reason?: string;
  process_status?: string;
  process_error?: string;
  process_reason?: string;
  content_source?: string;
  final_content_length?: number;
  source_content_length?: number;
  content_from_url?: boolean;
  url_fetch_attempted?: boolean;
  url_fetch_successful?: boolean;
}

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
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [expandedArticles, setExpandedArticles] = useState<Set<number>>(new Set());

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

  const handleViewDetail = (log: CrawlLog) => {
    setSelectedLog(log);
    setShowDetailModal(true);
    setExpandedArticles(new Set());
  };

  const handleCloseDetail = () => {
    setShowDetailModal(false);
    setSelectedLog(null);
    setExpandedArticles(new Set());
  };

  const toggleArticle = (index: number) => {
    setExpandedArticles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
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

  const getBreakdown = (log: CrawlLog): LogBreakdown | null => {
    if (!log.log_metadata) return null;
    const metadata = log.log_metadata as Record<string, unknown>;
    return (metadata.breakdown || {}) as LogBreakdown;
  };

  const getSkippedCount = (log: CrawlLog): number => {
    const breakdown = getBreakdown(log);
    return breakdown?.skipped_reasons?.total_skipped || 0;
  };

  const getFailedCount = (log: CrawlLog): number => {
    const breakdown = getBreakdown(log);
    return breakdown?.failed_reasons?.total_failed || 0;
  };

  const getArticleRecords = (log: CrawlLog): ArticleRecord[] => {
    if (!log.log_metadata) return [];
    const metadata = log.log_metadata as Record<string, unknown>;
    const records = metadata.parse_records;
    return Array.isArray(records) ? records as ArticleRecord[] : [];
  };

  const getStatusDisplay = (record: ArticleRecord) => {
    const status = record.process_status || record.status;
    switch (status) {
      case "created":
        return { label: "Created", color: "text-green-600", bg: "bg-green-50" };
      case "skipped_url_exists":
        return { label: "Skipped (URL exists)", color: "text-yellow-600", bg: "bg-yellow-50" };
      case "skipped_hash_exists":
        return { label: "Skipped (Duplicate)", color: "text-yellow-600", bg: "bg-yellow-50" };
      case "failed_parse":
        return { label: "Failed (Parse)", color: "text-red-600", bg: "bg-red-50" };
      case "failed_db":
        return { label: "Failed (Database)", color: "text-red-600", bg: "bg-red-50" };
      case "parsed":
        return { label: "Parsed", color: "text-blue-600", bg: "bg-blue-50" };
      default:
        return { label: status || "Unknown", color: "text-gray-600", bg: "bg-gray-50" };
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
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden sm:table-cell">
                    <div className="flex flex-col">
                      <span>Found</span>
                      <span className="text-xs text-muted">/ Created / Skipped / Failed</span>
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">{t.crawlLogs.startedAt}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">{t.crawlLogs.finishedAt}</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-ink">{t.crawlLogs.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {logs.map((log) => {
                  const skipped = getSkippedCount(log);
                  const failed = getFailedCount(log);
                  const hasIssues = skipped > 0 || failed > 0;
                  
                  return (
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
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-ink">{log.articles_found}</span>
                          <span className="text-sm text-muted">/</span>
                          <span className="text-sm font-medium text-green-600">{log.articles_created}</span>
                          {(skipped > 0 || failed > 0) && (
                            <>
                              <span className="text-sm text-muted">/</span>
                              {skipped > 0 && (
                                <span className="text-sm font-medium text-yellow-600">{skipped}</span>
                              )}
                              {skipped > 0 && failed > 0 && (
                                <span className="text-sm text-muted">/</span>
                              )}
                              {failed > 0 && (
                                <span className="text-sm font-medium text-red-600">{failed}</span>
                              )}
                            </>
                          )}
                          {hasIssues && (
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <span className="text-sm text-muted">{formatDate(log.started_at)}</span>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell">
                        <span className="text-sm text-muted">{formatDate(log.finished_at)}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleViewDetail(log)}
                          className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-muted hover:text-ink hover:bg-gray-100 transition-colors"
                          title="View details"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showDetailModal && selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <div className="flex items-center gap-3">
                <Info className="h-5 w-5 text-blue-600" />
                <h3 className="text-base font-semibold text-ink">Crawl Log Details</h3>
              </div>
              <button
                onClick={handleCloseDetail}
                className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted">Source</label>
                    <p className="text-ink mt-1">{getSourceName(selectedLog)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted">Status</label>
                    <p className="mt-1">{getStatusBadge(selectedLog.status)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="rounded-lg bg-blue-50 p-3">
                    <label className="text-xs font-medium text-blue-700">Found</label>
                    <p className="text-2xl font-bold text-blue-900">{selectedLog.articles_found}</p>
                  </div>
                  <div className="rounded-lg bg-green-50 p-3">
                    <label className="text-xs font-medium text-green-700">Created</label>
                    <p className="text-2xl font-bold text-green-900">{selectedLog.articles_created}</p>
                  </div>
                  <div className="rounded-lg bg-yellow-50 p-3">
                    <label className="text-xs font-medium text-yellow-700">Skipped</label>
                    <p className="text-2xl font-bold text-yellow-900">{getSkippedCount(selectedLog)}</p>
                  </div>
                  <div className="rounded-lg bg-red-50 p-3">
                    <label className="text-xs font-medium text-red-700">Failed</label>
                    <p className="text-2xl font-bold text-red-900">{getFailedCount(selectedLog)}</p>
                  </div>
                </div>

                {getBreakdown(selectedLog) && (
                  <div className="rounded-lg border border-line bg-gray-50 p-4">
                    <label className="text-sm font-medium text-muted block mb-2">Summary</label>
                    <p className="text-sm text-ink">
                      {getBreakdown(selectedLog)?.summary}
                    </p>
                    {getBreakdown(selectedLog)?.skipped_reasons && (
                      <div className="mt-3 flex flex-wrap gap-3 text-sm">
                        <span className="text-yellow-600">
                          URL exists: {getBreakdown(selectedLog)?.skipped_reasons?.url_already_exists || 0}
                        </span>
                        <span className="text-yellow-600">
                          Duplicate content: {getBreakdown(selectedLog)?.skipped_reasons?.content_hash_already_exists || 0}
                        </span>
                      </div>
                    )}
                    {getBreakdown(selectedLog)?.failed_reasons && (
                      <div className="mt-2 flex flex-wrap gap-3 text-sm">
                        <span className="text-red-600">
                          Parse failed: {getBreakdown(selectedLog)?.failed_reasons?.parse_failed || 0}
                        </span>
                        <span className="text-red-600">
                          DB failed: {getBreakdown(selectedLog)?.failed_reasons?.database_operation_failed || 0}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-muted">Started At</label>
                    <p className="text-ink mt-1">{formatDate(selectedLog.started_at)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted">Finished At</label>
                    <p className="text-ink mt-1">{formatDate(selectedLog.finished_at)}</p>
                  </div>
                </div>

                {selectedLog.error_message && (
                  <div>
                    <label className="text-sm font-medium text-muted">{t.crawlLogs.errorMessage}</label>
                    <div className="mt-1 p-4 bg-red-50 rounded-md border border-red-200 max-h-[200px] overflow-y-auto">
                      <pre className="text-sm text-red-800 whitespace-pre-wrap break-words">
                        {selectedLog.error_message}
                      </pre>
                    </div>
                  </div>
                )}

                {getArticleRecords(selectedLog).length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-muted block mb-3">
                      Article Processing Details ({getArticleRecords(selectedLog).length} articles)
                    </label>
                    <div className="border border-line rounded-lg overflow-hidden">
                      <div className="max-h-[500px] overflow-y-auto">
                        {getArticleRecords(selectedLog).map((record, idx) => {
                          const status = getStatusDisplay(record);
                          const isExpanded = expandedArticles.has(idx);
                          
                          return (
                            <div key={idx} className={`border-b border-line last:border-b-0 ${status.bg}`}>
                              <button
                                onClick={() => toggleArticle(idx)}
                                className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-opacity-80 transition-colors"
                              >
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                  {isExpanded ? (
                                    <ChevronDown className="h-4 w-4 text-muted flex-shrink-0" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4 text-muted flex-shrink-0" />
                                  )}
                                  <span className="text-sm font-medium text-muted min-w-[2rem]">#{record.index + 1}</span>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-ink truncate">{record.title || "Untitled"}</p>
                                    <p className="text-xs text-muted truncate">{record.url}</p>
                                  </div>
                                </div>
                                <span className={`text-xs font-medium px-2 py-1 rounded ${status.color} bg-white/80 ml-2 flex-shrink-0`}>
                                  {status.label}
                                </span>
                              </button>
                              
                              {isExpanded && (
                                <div className="px-4 pb-3 pl-11 border-t border-line border-opacity-50">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                                    <div>
                                      <label className="text-xs font-medium text-muted">Title</label>
                                      <p className="text-sm text-ink break-words">{record.title || "Untitled"}</p>
                                    </div>
                                    <div>
                                      <label className="text-xs font-medium text-muted">URL</label>
                                      <p className="text-sm text-ink break-all">{record.url || "-"}</p>
                                    </div>
                                    <div>
                                      <label className="text-xs font-medium text-muted">Status</label>
                                      <p className={`text-sm ${status.color} font-medium`}>{status.label}</p>
                                    </div>
                                    <div>
                                      <label className="text-xs font-medium text-muted">Content Source</label>
                                      <p className="text-sm text-ink">
                                        {record.content_from_url ? "Article URL" : "Feed/API"}
                                        {record.content_source && (
                                          <span className="text-muted"> ({record.content_source})</span>
                                        )}
                                      </p>
                                    </div>
                                    {record.final_content_length !== undefined && (
                                      <div>
                                        <label className="text-xs font-medium text-muted">Final Content Length</label>
                                        <p className="text-sm text-ink">{record.final_content_length.toLocaleString()} chars</p>
                                      </div>
                                    )}
                                    {record.source_content_length !== undefined && (
                                      <div>
                                        <label className="text-xs font-medium text-muted">Source Content Length</label>
                                        <p className="text-sm text-ink">{record.source_content_length.toLocaleString()} chars</p>
                                      </div>
                                    )}
                                    <div>
                                      <label className="text-xs font-medium text-muted">URL Fetch Attempted</label>
                                      <p className="text-sm text-ink">{record.url_fetch_attempted ? "Yes" : "No"}</p>
                                    </div>
                                    {record.url_fetch_attempted && (
                                      <div>
                                        <label className="text-xs font-medium text-muted">URL Fetch Successful</label>
                                        <p className={`text-sm ${record.url_fetch_successful ? "text-green-600" : "text-red-600"}`}>
                                          {record.url_fetch_successful ? "Yes" : "No"}
                                        </p>
                                      </div>
                                    )}
                                  </div>
                                  
                                  {(record.reason || record.process_reason) && (
                                    <div className="mt-3">
                                      <label className="text-xs font-medium text-muted">Reason</label>
                                      <p className="text-sm text-yellow-700 bg-yellow-50 px-3 py-2 rounded mt-1">
                                        {record.reason || record.process_reason}
                                      </p>
                                    </div>
                                  )}
                                  
                                  {(record.error_message || record.process_error) && (
                                    <div className="mt-3">
                                      <label className="text-xs font-medium text-muted">Error</label>
                                      <div className="text-sm text-red-700 bg-red-50 px-3 py-2 rounded mt-1 overflow-x-auto">
                                        <pre className="whitespace-pre-wrap break-words">
                                          {record.error_message || record.process_error}
                                        </pre>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {selectedLog.log_metadata && (
                  <div>
                    <label className="text-sm font-medium text-muted block mb-2">Raw Metadata (JSON)</label>
                    <div className="rounded-lg border border-line bg-gray-50 p-3 max-h-[300px] overflow-y-auto">
                      <pre className="text-xs text-ink whitespace-pre-wrap break-words">
                        {JSON.stringify(selectedLog.log_metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end border-t border-line px-5 py-4">
              <button
                onClick={handleCloseDetail}
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
