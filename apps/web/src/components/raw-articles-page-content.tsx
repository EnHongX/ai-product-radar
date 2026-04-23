"use client";

import { useEffect, useState } from "react";
import { Eye, Trash2, ExternalLink, X } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { useLanguage } from "@/i18n";
import type { RawArticle, RawArticleDetail, Company, Source } from "@/lib/api";
import { fetchRawArticles, fetchRawArticle, deleteRawArticle, fetchCompanies, fetchSources } from "@/lib/api";

export function RawArticlesPageContent() {
  const { t } = useLanguage();
  const [articles, setArticles] = useState<RawArticle[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [filterCompanyId, setFilterCompanyId] = useState<number | undefined>(undefined);
  const [filterSourceId, setFilterSourceId] = useState<number | undefined>(undefined);
  
  const [selectedArticle, setSelectedArticle] = useState<RawArticleDetail | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [companiesData, sourcesData] = await Promise.all([
        fetchCompanies(),
        fetchSources(),
      ]);
      setCompanies(companiesData);
      setSources(sourcesData);
      
      const articlesData = await fetchRawArticles(filterSourceId, filterCompanyId, 50, 0);
      setArticles(articlesData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load articles");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterCompanyId, filterSourceId]);

  const handleViewDetail = async (article: RawArticle) => {
    try {
      setDetailLoading(true);
      setShowDetailModal(true);
      const detail = await fetchRawArticle(article.id);
      setSelectedArticle(detail);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load article detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetail = () => {
    setShowDetailModal(false);
    setSelectedArticle(null);
  };

  const handleDeleteClick = async (article: RawArticle) => {
    if (!window.confirm(t.rawArticles.confirmDelete)) {
      return;
    }

    try {
      await deleteRawArticle(article.id);
      setSuccessMessage(t.rawArticles.deleteSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete article");
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleString();
  };

  const truncateUrl = (url: string, maxLength: number = 40) => {
    if (url.length <= maxLength) return url;
    return url.substring(0, maxLength - 3) + "...";
  };

  const getCompanyName = (article: RawArticle) => {
    if (article.company?.name) return article.company.name;
    return "-";
  };

  const getSourceName = (article: RawArticle) => {
    if (article.source?.name) return article.source.name;
    const source = sources.find(s => s.id === article.source_id);
    return source?.name || "-";
  };

  const filteredSources = filterCompanyId
    ? sources.filter(s => s.company_id === filterCompanyId)
    : sources;

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{t.rawArticles.title}</h2>
        </div>

        <div className="flex flex-wrap items-center gap-4 px-5 py-3 border-b border-line bg-gray-50">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.rawArticles.filterByCompany}:</label>
            <select
              value={filterCompanyId === undefined ? "" : filterCompanyId}
              onChange={(e) => {
                setFilterCompanyId(e.target.value === "" ? undefined : parseInt(e.target.value));
                setFilterSourceId(undefined);
              }}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.rawArticles.allCompanies}</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.rawArticles.filterBySource}:</label>
            <select
              value={filterSourceId === undefined ? "" : filterSourceId}
              onChange={(e) => setFilterSourceId(e.target.value === "" ? undefined : parseInt(e.target.value))}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.rawArticles.allSources}</option>
              {filteredSources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {successMessage && (
          <div className="mx-5 mt-4 rounded-md bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-800">
            {successMessage}
          </div>
        )}

        {error && (
          <div className="mx-5 mt-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {loading ? (
          <div className="px-5 py-8 text-center text-muted">{t.common.loading}</div>
        ) : articles.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <p className="text-muted">{t.rawArticles.noArticles}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.rawArticles.articleTitle}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden md:table-cell">{t.rawArticles.company}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">{t.rawArticles.source}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.rawArticles.url}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden sm:table-cell">{t.rawArticles.publishedAt}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden md:table-cell">{t.rawArticles.fetchedAt}</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-ink">{t.rawArticles.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {articles.map((article) => (
                  <tr key={article.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-ink truncate max-w-[200px]" title={article.title}>
                          {article.title}
                        </span>
                        <span className="text-xs text-muted sm:hidden">
                          {getCompanyName(article)} / {getSourceName(article)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-sm text-muted">{getCompanyName(article)}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <span className="text-sm text-muted">{getSourceName(article)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-accent hover:underline flex items-center gap-1 max-w-[250px]"
                        title={article.url}
                      >
                        <span className="truncate">{truncateUrl(article.url)}</span>
                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                      </a>
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      <span className="text-sm text-muted">{formatDate(article.published_at)}</span>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <span className="text-sm text-muted">{formatDate(article.fetched_at)}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="inline-flex items-center gap-1">
                        <button
                          onClick={() => handleViewDetail(article)}
                          className="rounded p-1.5 text-muted hover:text-blue-600 hover:bg-blue-50 transition-colors"
                          title={t.rawArticles.view}
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(article)}
                          className="rounded p-1.5 text-muted hover:text-red-600 hover:bg-red-50 transition-colors"
                          title={t.rawArticles.delete}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showDetailModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <h3 className="text-base font-semibold text-ink">{t.rawArticles.viewDetail}</h3>
              <button
                onClick={handleCloseDetail}
                className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {detailLoading ? (
                <div className="text-center py-8 text-muted">{t.common.loading}</div>
              ) : selectedArticle ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-muted">{t.rawArticles.articleTitle}</label>
                    <p className="text-ink font-medium mt-1">{selectedArticle.title}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted">{t.rawArticles.company}</label>
                      <p className="text-ink mt-1">{getCompanyName(selectedArticle)}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted">{t.rawArticles.source}</label>
                      <p className="text-ink mt-1">{getSourceName(selectedArticle)}</p>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-muted">{t.rawArticles.url}</label>
                    <a
                      href={selectedArticle.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:underline flex items-center gap-1 mt-1 break-all"
                    >
                      {selectedArticle.url}
                      <ExternalLink className="h-4 w-4 flex-shrink-0" />
                    </a>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted">{t.rawArticles.author}</label>
                      <p className="text-ink mt-1">{selectedArticle.author || "-"}</p>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-muted">{t.rawArticles.publishedAt}</label>
                      <p className="text-ink mt-1">{formatDate(selectedArticle.published_at)}</p>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-muted">{t.rawArticles.fetchedAt}</label>
                    <p className="text-ink mt-1">{formatDate(selectedArticle.fetched_at)}</p>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-muted">{t.rawArticles.content}</label>
                    <div className="mt-1 p-4 bg-gray-50 rounded-md border border-line max-h-[400px] overflow-y-auto">
                      {selectedArticle.content ? (
                        <div
                          className="text-sm text-ink prose prose-sm max-w-none"
                          dangerouslySetInnerHTML={{ __html: selectedArticle.content }}
                        />
                      ) : (
                        <p className="text-muted">{t.common.noData}</p>
                      )}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            <div className="flex justify-end border-t border-line px-5 py-4">
              <button
                onClick={handleCloseDetail}
                className="inline-flex items-center gap-2 rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-ink hover:bg-gray-200 transition-colors"
              >
                {t.rawArticles.close}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
