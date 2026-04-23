"use client";

import { useState } from "react";
import { X } from "lucide-react";

import { useLanguage } from "@/i18n";
import type { Source, SourceCreate, SourceUpdate, Company } from "@/lib/api";

interface SourceFormProps {
  source?: Source | null;
  companies: Company[];
  onSubmit: (data: SourceCreate | SourceUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function SourceForm({ source, companies, onSubmit, onCancel, isSubmitting }: SourceFormProps) {
  const { t } = useLanguage();
  const isEdit = !!source;

  const [formData, setFormData] = useState<SourceCreate | SourceUpdate>({
    company_id: source?.company_id || (companies.length > 0 ? companies[0].id : 0),
    name: source?.name || "",
    url: source?.url || "",
    source_type: source?.source_type || "",
    parse_strategy: source?.parse_strategy || "",
    enabled: source?.enabled ?? true,
    crawl_interval_hours: source?.crawl_interval_hours || 24,
  });

  const handleChange = (field: string, value: string | number | boolean) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: SourceCreate | SourceUpdate = {};

    if (formData.company_id !== undefined && formData.company_id > 0) {
      data.company_id = formData.company_id;
    }
    if (formData.name) {
      data.name = formData.name;
    }
    if (formData.url) {
      data.url = formData.url;
    }
    if (formData.source_type) {
      data.source_type = formData.source_type;
    }
    if (formData.parse_strategy) {
      data.parse_strategy = formData.parse_strategy;
    }
    if (formData.enabled !== undefined) {
      data.enabled = formData.enabled;
    }
    if (formData.crawl_interval_hours !== undefined && formData.crawl_interval_hours > 0) {
      data.crawl_interval_hours = formData.crawl_interval_hours;
    }

    await onSubmit(data);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-ink">
            {isEdit ? t.sources.editSource : t.sources.newSource}
          </h3>
          <button
            onClick={onCancel}
            className="text-muted hover:text-ink transition-colors"
            disabled={isSubmitting}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                {t.sources.company} <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.company_id || 0}
                onChange={(e) => handleChange("company_id", parseInt(e.target.value) || 0)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                required
                disabled={isSubmitting}
              >
                <option value={0}>{t.sources.selectCompany}</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                {t.sources.name} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name || ""}
                onChange={(e) => handleChange("name", e.target.value)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                placeholder="e.g., OpenAI Blog"
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              {t.sources.url} <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              value={formData.url || ""}
              onChange={(e) => handleChange("url", e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="https://example.com/feed"
              required
              disabled={isSubmitting}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                {t.sources.sourceType} <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.source_type || ""}
                onChange={(e) => handleChange("source_type", e.target.value)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                required
                disabled={isSubmitting}
              >
                <option value="">-- Select Type --</option>
                <option value="blog">Blog</option>
                <option value="rss">RSS Feed</option>
                <option value="newsletter">Newsletter</option>
                <option value="social">Social Media</option>
                <option value="documentation">Documentation</option>
                <option value="changelog">Changelog</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                {t.sources.parseStrategy} <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.parse_strategy || ""}
                onChange={(e) => handleChange("parse_strategy", e.target.value)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                required
                disabled={isSubmitting}
              >
                <option value="">-- Select Strategy --</option>
                <option value="rss">RSS Parser</option>
                <option value="html">HTML Scraper</option>
                <option value="json">JSON API</option>
                <option value="custom">Custom Script</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                {t.sources.crawlInterval}
              </label>
              <input
                type="number"
                min={1}
                value={formData.crawl_interval_hours || 24}
                onChange={(e) => handleChange("crawl_interval_hours", parseInt(e.target.value) || 24)}
                className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ink mb-1">
                {t.sources.enabled}
              </label>
              <div className="flex items-center h-10">
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.enabled ?? true}
                    onChange={(e) => handleChange("enabled", e.target.checked)}
                    className="sr-only peer"
                    disabled={isSubmitting}
                  />
                  <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                  <span className="ms-3 text-sm font-medium text-ink">
                    {(formData.enabled ?? true) ? t.sources.enabledTrue : t.sources.enabledFalse}
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              {t.sources.cancel}
            </button>
            <button
              type="submit"
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? t.common.loading : t.sources.save}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
