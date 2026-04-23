"use client";

import { useEffect, useState } from "react";
import { Plus, Edit2, Trash2, Power, PowerOff, ExternalLink, MoreVertical, RefreshCw } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { SourceForm } from "@/components/source-form";
import { useLanguage } from "@/i18n";
import type { Source, SourceCreate, SourceUpdate, Company, SourceDeleteCheck, SourceType, CrawlTriggerResponse } from "@/lib/api";
import { fetchSources, createSource, updateSource, deleteSource, checkSourceDelete, fetchCompanies, fetchSourceTypes, triggerCrawl } from "@/lib/api";

export function SourcesPageContent() {
  const { t } = useLanguage();
  const [sources, setSources] = useState<Source[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [sourceTypes, setSourceTypes] = useState<SourceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingSource, setEditingSource] = useState<Source | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  const [filterCompanyId, setFilterCompanyId] = useState<number | undefined>(undefined);
  const [filterEnabled, setFilterEnabled] = useState<boolean | undefined>(undefined);
  const [dropdownOpen, setDropdownOpen] = useState<number | null>(null);
  const [crawlingSourceId, setCrawlingSourceId] = useState<number | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [companiesData, sourcesData, typesData] = await Promise.all([
        fetchCompanies(),
        fetchSources(filterCompanyId, filterEnabled),
        fetchSourceTypes(true),
      ]);
      setCompanies(companiesData);
      setSources(sourcesData);
      setSourceTypes(typesData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterCompanyId, filterEnabled]);

  useEffect(() => {
    const handleClickOutside = () => setDropdownOpen(null);
    if (dropdownOpen !== null) {
      document.addEventListener("click", handleClickOutside);
      return () => document.removeEventListener("click", handleClickOutside);
    }
  }, [dropdownOpen]);

  const handleAddClick = () => {
    setEditingSource(null);
    setShowForm(true);
  };

  const handleEditClick = (source: Source) => {
    setEditingSource(source);
    setShowForm(true);
    setDropdownOpen(null);
  };

  const handleCrawlClick = async (source: Source) => {
    setDropdownOpen(null);
    
    if (!source.enabled) {
      setError(t.sources.crawlDisabled);
      setTimeout(() => setError(null), 5000);
      return;
    }
    
    if (source.parse_strategy !== "rss_feed") {
      setError(t.sources.crawlNotRss);
      setTimeout(() => setError(null), 5000);
      return;
    }
    
    try {
      setCrawlingSourceId(source.id);
      await triggerCrawl(source.id);
      setSuccessMessage(t.sources.crawlSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger crawl");
    } finally {
      setCrawlingSourceId(null);
    }
  };

  const handleToggleStatus = async (source: Source) => {
    try {
      await updateSource(source.id, { enabled: !source.enabled });
      setSuccessMessage(t.sources.statusChangeSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update source status");
    }
    setDropdownOpen(null);
  };

  const handleDeleteClick = async (source: Source) => {
    setDropdownOpen(null);
    
    try {
      const check: SourceDeleteCheck = await checkSourceDelete(source.id);
      
      if (!check.can_delete) {
        setError(t.sources.deleteWithDataWarning);
        setTimeout(() => setError(null), 5000);
        return;
      }
      
      if (!window.confirm(t.sources.confirmDelete)) {
        return;
      }

      await deleteSource(source.id);
      setSuccessMessage(t.sources.deleteSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source");
    }
  };

  const handleFormSubmit = async (data: SourceCreate | SourceUpdate) => {
    try {
      setIsSubmitting(true);
      setError(null);

      if (editingSource) {
        await updateSource(editingSource.id, data);
      } else {
        await createSource(data as SourceCreate);
      }

      setSuccessMessage(t.sources.saveSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      setShowForm(false);
      setEditingSource(null);
      loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save source");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingSource(null);
  };

  const getCompanyName = (source: Source) => {
    if (source.company?.name) return source.company.name;
    const company = companies.find(c => c.id === source.company_id);
    return company?.name || "-";
  };

  const handleDropdownClick = (e: React.MouseEvent, sourceId: number) => {
    e.stopPropagation();
    setDropdownOpen(dropdownOpen === sourceId ? null : sourceId);
  };

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{t.sources.title}</h2>
          <button
            onClick={handleAddClick}
            className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            {t.sources.addSource}
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-4 px-5 py-3 border-b border-line bg-gray-50">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.sources.filterByCompany}:</label>
            <select
              value={filterCompanyId === undefined ? "" : filterCompanyId}
              onChange={(e) => setFilterCompanyId(e.target.value === "" ? undefined : parseInt(e.target.value))}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.sources.allCompanies}</option>
              {companies.map((company) => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted">{t.sources.filterByStatus}:</label>
            <select
              value={filterEnabled === undefined ? "" : filterEnabled.toString()}
              onChange={(e) => {
                const value = e.target.value;
                setFilterEnabled(value === "" ? undefined : value === "true");
              }}
              className="rounded-md border border-line px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">{t.sources.allStatus}</option>
              <option value="true">{t.sources.enabledTrue}</option>
              <option value="false">{t.sources.enabledFalse}</option>
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
        ) : sources.length === 0 ? (
          <div className="px-5 py-12 text-center">
            <p className="text-muted mb-4">{t.sources.noSources}</p>
            <button
              onClick={handleAddClick}
              className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              {t.sources.addSource}
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.sources.name}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden md:table-cell">{t.sources.url}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.sources.company}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink hidden lg:table-cell">{t.sources.sourceType}</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-ink">{t.sources.enabled}</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-ink">{t.sources.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {sources.map((source) => (
                  <tr key={source.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-ink">{source.name}</span>
                        <span className="text-xs text-muted hidden sm:inline md:hidden truncate max-w-[200px]">
                          {source.url}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell">
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-accent hover:underline flex items-center gap-1 max-w-[250px] truncate"
                        title={source.url}
                      >
                        <span className="truncate">{source.url}</span>
                        <ExternalLink className="h-3 w-3 flex-shrink-0" />
                      </a>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-muted">{getCompanyName(source)}</span>
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                        {source.source_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          source.enabled
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {source.enabled ? (
                          <Power className="h-3 w-3 mr-1" />
                        ) : (
                          <PowerOff className="h-3 w-3 mr-1" />
                        )}
                        {source.enabled ? t.sources.enabledTrue : t.sources.enabledFalse}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right relative">
                      <div className="hidden sm:inline-flex items-center gap-1">
                        <button
                          onClick={() => handleCrawlClick(source)}
                          disabled={crawlingSourceId === source.id || !source.enabled || source.parse_strategy !== "rss_feed"}
                          className={`rounded p-1.5 transition-colors ${
                            crawlingSourceId === source.id
                              ? "text-accent animate-spin"
                              : !source.enabled || source.parse_strategy !== "rss_feed"
                              ? "text-gray-300 cursor-not-allowed"
                              : "text-muted hover:text-blue-600 hover:bg-blue-50"
                          }`}
                          title={t.sources.crawl}
                        >
                          <RefreshCw className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleToggleStatus(source)}
                          className={`rounded p-1.5 text-muted hover:bg-gray-100 transition-colors ${
                            source.enabled
                              ? "hover:text-orange-600 hover:bg-orange-50"
                              : "hover:text-green-600 hover:bg-green-50"
                          }`}
                          title={source.enabled ? t.sources.enabledFalse : t.sources.enabledTrue}
                        >
                          {source.enabled ? (
                            <PowerOff className="h-4 w-4" />
                          ) : (
                            <Power className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEditClick(source)}
                          className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
                          title={t.sources.edit}
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(source)}
                          className="rounded p-1.5 text-muted hover:text-red-600 hover:bg-red-50 transition-colors"
                          title={t.sources.delete}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>

                      <div className="sm:hidden relative">
                        <button
                          onClick={(e) => handleDropdownClick(e, source.id)}
                          className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </button>
                        
                        {dropdownOpen === source.id && (
                          <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-md shadow-lg border border-line z-10">
                            <button
                              onClick={() => handleCrawlClick(source)}
                              disabled={crawlingSourceId === source.id || !source.enabled || source.parse_strategy !== "rss_feed"}
                              className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${
                                !source.enabled || source.parse_strategy !== "rss_feed"
                                  ? "text-gray-400 cursor-not-allowed"
                                  : "text-ink hover:bg-gray-50"
                              }`}
                            >
                              <RefreshCw className={`h-4 w-4 ${crawlingSourceId === source.id ? "animate-spin" : ""}`} /> {t.sources.crawl}
                            </button>
                            <button
                              onClick={() => handleToggleStatus(source)}
                              className="w-full text-left px-4 py-2 text-sm text-ink hover:bg-gray-50 flex items-center gap-2"
                            >
                              {source.enabled ? (
                                <><PowerOff className="h-4 w-4" /> {t.sources.enabledFalse}</>
                              ) : (
                                <><Power className="h-4 w-4" /> {t.sources.enabledTrue}</>
                              )}
                            </button>
                            <button
                              onClick={() => handleEditClick(source)}
                              className="w-full text-left px-4 py-2 text-sm text-ink hover:bg-gray-50 flex items-center gap-2"
                            >
                              <Edit2 className="h-4 w-4" /> {t.sources.edit}
                            </button>
                            <button
                              onClick={() => handleDeleteClick(source)}
                              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                            >
                              <Trash2 className="h-4 w-4" /> {t.sources.delete}
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showForm && (
        <SourceForm
          source={editingSource}
          companies={companies}
          sourceTypes={sourceTypes}
          onSubmit={handleFormSubmit}
          onCancel={handleFormCancel}
          isSubmitting={isSubmitting}
        />
      )}
    </AdminLayout>
  );
}
