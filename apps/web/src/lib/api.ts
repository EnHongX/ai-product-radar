const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type Company = {
  id: number;
  name: string;
  slug: string;
  website: string | null;
  country: string | null;
  company_type: string;
  logo_url: string | null;
  description: string | null;
};

export type CompanyCreate = {
  name: string;
  website?: string | null;
  country?: string | null;
  company_type: string;
  logo_url?: string | null;
  description?: string | null;
};

export type CompanyUpdate = {
  name?: string;
  website?: string | null;
  country?: string | null;
  company_type?: string;
  logo_url?: string | null;
  description?: string | null;
};

export async function fetchCompanies(): Promise<Company[]> {
  const response = await fetch(`${API_BASE_URL}/api/companies`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch companies");
  }

  return response.json();
}

export async function fetchCompany(id: number): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/api/companies/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch company");
  }

  return response.json();
}

export async function createCompany(data: CompanyCreate): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/api/companies`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to create company");
  }

  return response.json();
}

export async function updateCompany(id: number, data: CompanyUpdate): Promise<Company> {
  const response = await fetch(`${API_BASE_URL}/api/companies/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to update company");
  }

  return response.json();
}

export async function deleteCompany(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/companies/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to delete company");
  }
}
