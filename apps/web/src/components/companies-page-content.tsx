"use client";

import { useEffect, useState } from "react";
import { Plus, Edit2, Trash2 } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { CompanyForm } from "@/components/company-form";
import { useLanguage } from "@/i18n";
import type { Company, CompanyCreate, CompanyUpdate, CompanyType } from "@/lib/api";
import { fetchCompanies, createCompany, updateCompany, deleteCompany, fetchCompanyTypes } from "@/lib/api";

export function CompaniesPageContent() {
  const { t } = useLanguage();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyTypes, setCompanyTypes] = useState<CompanyType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadCompanies = async () => {
    try {
      setLoading(true);
      const [companiesData, typesData] = await Promise.all([
        fetchCompanies(),
        fetchCompanyTypes(true),
      ]);
      setCompanies(companiesData);
      setCompanyTypes(typesData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCompanies();
  }, []);

  const handleAddClick = () => {
    setEditingCompany(null);
    setShowForm(true);
  };

  const handleEditClick = (company: Company) => {
    setEditingCompany(company);
    setShowForm(true);
  };

  const handleDeleteClick = async (company: Company) => {
    if (!window.confirm(t.companies.confirmDelete)) {
      return;
    }

    try {
      await deleteCompany(company.id);
      setSuccessMessage(t.companies.deleteSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadCompanies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete company");
    }
  };

  const handleFormSubmit = async (data: CompanyCreate | CompanyUpdate) => {
    try {
      setIsSubmitting(true);
      setError(null);

      if (editingCompany) {
        await updateCompany(editingCompany.id, data);
      } else {
        await createCompany(data as CompanyCreate);
      }

      setSuccessMessage(t.companies.saveSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      setShowForm(false);
      setEditingCompany(null);
      loadCompanies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save company");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingCompany(null);
  };

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{t.companies.title}</h2>
          <button
            onClick={handleAddClick}
            className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            {t.companies.addCompany}
          </button>
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
        ) : companies.length === 0 ? (
          <div className="px-5 py-8 text-center text-muted">{t.companies.noCompanies}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line bg-gray-50">
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{t.companies.name}</th>
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{t.companies.companyType}</th>
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{t.companies.country}</th>
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{t.companies.website}</th>
                  <th className="px-5 py-3 text-right text-sm font-medium text-ink">{t.companies.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {companies.map((company) => (
                  <tr key={company.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 text-sm text-ink">{company.name}</td>
                    <td className="px-5 py-3 text-sm text-muted">{company.company_type}</td>
                    <td className="px-5 py-3 text-sm text-muted">{company.country || "-"}</td>
                    <td className="px-5 py-3 text-sm text-muted">
                      {company.website ? (
                        <a
                          href={company.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent hover:underline"
                        >
                          {company.website}
                        </a>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleEditClick(company)}
                          className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
                          title={t.companies.edit}
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(company)}
                          className="rounded p-1.5 text-muted hover:text-red-600 hover:bg-red-50 transition-colors"
                          title={t.companies.delete}
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

      {showForm && (
        <CompanyForm
          company={editingCompany}
          companyTypes={companyTypes}
          onSubmit={handleFormSubmit}
          onCancel={handleFormCancel}
          isSubmitting={isSubmitting}
        />
      )}
    </AdminLayout>
  );
}
