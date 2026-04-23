"use client";

import { useEffect, useState } from "react";
import { Plus, Edit2, Trash2, ToggleLeft, ToggleRight } from "lucide-react";

import { AdminLayout } from "@/components/admin-layout";
import { TypeForm } from "@/components/type-form";
import { useLanguage } from "@/i18n";
import type { SourceType, SourceTypeCreate, SourceTypeUpdate } from "@/lib/api";
import { fetchSourceTypes, createSourceType, updateSourceType, deleteSourceType } from "@/lib/api";

export function SourceTypesPageContent() {
  const { t } = useLanguage();
  const [types, setTypes] = useState<SourceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingType, setEditingType] = useState<SourceType | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const typeT = t.sourceTypes;

  const loadTypes = async () => {
    try {
      setLoading(true);
      const data = await fetchSourceTypes();
      setTypes(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load source types");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTypes();
  }, []);

  const handleAddClick = () => {
    setEditingType(null);
    setShowForm(true);
  };

  const handleEditClick = (typeItem: SourceType) => {
    setEditingType(typeItem);
    setShowForm(true);
  };

  const handleDeleteClick = async (typeItem: SourceType) => {
    if (!window.confirm(typeT.confirmDelete)) {
      return;
    }

    try {
      await deleteSourceType(typeItem.id);
      setSuccessMessage(typeT.deleteSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source type");
    }
  };

  const handleToggleStatus = async (typeItem: SourceType) => {
    try {
      await updateSourceType(typeItem.id, { enabled: !typeItem.enabled });
      setSuccessMessage(typeT.statusChangeSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update status");
    }
  };

  const handleFormSubmit = async (data: SourceTypeCreate) => {
    try {
      setIsSubmitting(true);
      setError(null);

      if (editingType) {
        const updateData: SourceTypeUpdate = { name: data.name };
        await updateSourceType(editingType.id, updateData);
      } else {
        await createSourceType(data);
      }

      setSuccessMessage(typeT.saveSuccess);
      setTimeout(() => setSuccessMessage(null), 3000);
      setShowForm(false);
      setEditingType(null);
      loadTypes();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save source type");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingType(null);
  };

  return (
    <AdminLayout>
      <div className="rounded-lg border border-line bg-white">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="text-base font-semibold text-ink">{typeT.title}</h2>
          <button
            onClick={handleAddClick}
            className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            {typeT.addType}
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
        ) : types.length === 0 ? (
          <div className="px-5 py-8 text-center text-muted">{typeT.noTypes}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-line bg-gray-50">
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{typeT.name}</th>
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{typeT.slug}</th>
                  <th className="px-5 py-3 text-left text-sm font-medium text-ink">{typeT.status}</th>
                  <th className="px-5 py-3 text-right text-sm font-medium text-ink">{typeT.actions}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {types.map((typeItem) => (
                  <tr key={typeItem.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 text-sm text-ink">{typeItem.name}</td>
                    <td className="px-5 py-3 text-sm text-muted">{typeItem.slug}</td>
                    <td className="px-5 py-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          typeItem.enabled
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {typeItem.enabled ? typeT.enabled : typeT.disabled}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleToggleStatus(typeItem)}
                          className={`rounded p-1.5 transition-colors ${
                            typeItem.enabled
                              ? "text-muted hover:text-amber-600 hover:bg-amber-50"
                              : "text-muted hover:text-emerald-600 hover:bg-emerald-50"
                          }`}
                          title={typeT.toggleStatus}
                        >
                          {typeItem.enabled ? (
                            <ToggleRight className="h-4 w-4" />
                          ) : (
                            <ToggleLeft className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEditClick(typeItem)}
                          className="rounded p-1.5 text-muted hover:text-ink hover:bg-gray-100 transition-colors"
                          title={typeT.edit}
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(typeItem)}
                          className="rounded p-1.5 text-muted hover:text-red-600 hover:bg-red-50 transition-colors"
                          title={typeT.delete}
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
        <TypeForm
          typeItem={editingType}
          typeKey="sourceTypes"
          onSubmit={handleFormSubmit}
          onCancel={handleFormCancel}
          isSubmitting={isSubmitting}
        />
      )}
    </AdminLayout>
  );
}
