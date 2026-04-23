"use client";

import { useState } from "react";
import { X } from "lucide-react";

import { useLanguage } from "@/i18n";
import type { Company, CompanyCreate, CompanyUpdate, CompanyType } from "@/lib/api";

interface CompanyFormProps {
  company?: Company | null;
  companyTypes: CompanyType[];
  onSubmit: (data: CompanyCreate | CompanyUpdate) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function CompanyForm({ company, companyTypes, onSubmit, onCancel, isSubmitting }: CompanyFormProps) {
  const { t } = useLanguage();
  const isEdit = !!company;

  const getDefaultCompanyType = (): string => {
    if (company?.company_type) {
      const matchedType = companyTypes.find(
        (t) => t.name === company.company_type || t.slug === company.company_type
      );
      if (matchedType) {
        return matchedType.name;
      }
    }
    return companyTypes.length > 0 ? companyTypes[0].name : "";
  };

  const [formData, setFormData] = useState<CompanyCreate | CompanyUpdate>({
    name: company?.name || "",
    website: company?.website || "",
    country: company?.country || "",
    company_type: getDefaultCompanyType(),
    logo_url: company?.logo_url || "",
    description: company?.description || "",
  });

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value || null,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data: CompanyCreate | CompanyUpdate = {};

    if (formData.name) {
      data.name = formData.name;
    }
    if (formData.website !== undefined) {
      data.website = formData.website || null;
    }
    if (formData.country !== undefined) {
      data.country = formData.country || null;
    }
    if (formData.company_type) {
      data.company_type = formData.company_type;
    }
    if (formData.logo_url !== undefined) {
      data.logo_url = formData.logo_url || null;
    }
    if (formData.description !== undefined) {
      data.description = formData.description || null;
    }

    await onSubmit(data);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-ink">
            {isEdit ? t.companies.editCompany : t.companies.newCompany}
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
          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              {t.companies.name} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name || ""}
              onChange={(e) => handleChange("name", e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">
              {t.companies.companyType} <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.company_type || ""}
              onChange={(e) => handleChange("company_type", e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              required
              disabled={isSubmitting}
            >
              <option value="">-- Select Type --</option>
              {companyTypes.map((type) => (
                <option key={type.id} value={type.name}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">{t.companies.website}</label>
            <input
              type="url"
              value={formData.website || ""}
              onChange={(e) => handleChange("website", e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="https://example.com"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">{t.companies.country}</label>
            <input
              type="text"
              value={formData.country || ""}
              onChange={(e) => handleChange("country", e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">{t.companies.logoUrl}</label>
            <input
              type="url"
              value={formData.logo_url || ""}
              onChange={(e) => handleChange("logo_url", e.target.value)}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="https://example.com/logo.png"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1">{t.companies.description}</label>
            <textarea
              value={formData.description || ""}
              onChange={(e) => handleChange("description", e.target.value)}
              rows={3}
              className="w-full rounded-md border border-line px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent resize-none"
              disabled={isSubmitting}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              {t.companies.cancel}
            </button>
            <button
              type="submit"
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? t.common.loading : t.companies.save}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
