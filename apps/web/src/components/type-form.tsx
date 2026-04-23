"use client";

import { useState } from "react";
import { X } from "lucide-react";

import { useLanguage } from "@/i18n";

interface TypeFormProps {
  typeItem?: { id: number; name: string; slug: string; enabled: boolean } | null;
  typeKey: "companyTypes" | "sourceTypes";
  onSubmit: (data: { name: string }) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export function TypeForm({ typeItem, typeKey, onSubmit, onCancel, isSubmitting }: TypeFormProps) {
  const { t } = useLanguage();
  const isEdit = !!typeItem;
  const typeT = t[typeKey];

  const [formData, setFormData] = useState<{ name: string }>({
    name: typeItem?.name || "",
  });

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-ink">
            {isEdit ? typeT.editType : typeT.newType}
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
              {typeT.name} <span className="text-red-500">*</span>
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

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              {typeT.cancel}
            </button>
            <button
              type="submit"
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? t.common.loading : typeT.save}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
