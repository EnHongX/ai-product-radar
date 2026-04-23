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

export type SourceCompany = {
  id: number;
  name: string;
};

export type Source = {
  id: number;
  company_id: number;
  name: string;
  url: string;
  source_type: string;
  parse_strategy: string;
  enabled: boolean;
  crawl_interval_hours: number;
  last_crawled_at: string | null;
  created_at: string;
  updated_at: string;
  company?: SourceCompany | null;
};

export type SourceCreate = {
  company_id: number;
  name: string;
  url: string;
  source_type: string;
  parse_strategy: string;
  enabled?: boolean;
  crawl_interval_hours?: number;
};

export type SourceUpdate = {
  company_id?: number;
  name?: string;
  url?: string;
  source_type?: string;
  parse_strategy?: string;
  enabled?: boolean;
  crawl_interval_hours?: number;
};

export type SourceDeleteCheck = {
  can_delete: boolean;
  raw_articles_count: number;
  product_releases_count: number;
  message: string;
};

export async function fetchSources(companyId?: number, enabled?: boolean): Promise<Source[]> {
  let url = `${API_BASE_URL}/api/sources`;
  const params = new URLSearchParams();
  if (companyId !== undefined) {
    params.append("company_id", companyId.toString());
  }
  if (enabled !== undefined) {
    params.append("enabled", enabled.toString());
  }
  if (params.toString()) {
    url += `?${params.toString()}`;
  }

  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch sources");
  }

  return response.json();
}

export async function fetchSource(id: number): Promise<Source> {
  const response = await fetch(`${API_BASE_URL}/api/sources/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch source");
  }

  return response.json();
}

export async function checkSourceDelete(id: number): Promise<SourceDeleteCheck> {
  const response = await fetch(`${API_BASE_URL}/api/sources/${id}/delete-check`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to check source delete status");
  }

  return response.json();
}

export async function createSource(data: SourceCreate): Promise<Source> {
  const response = await fetch(`${API_BASE_URL}/api/sources`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to create source");
  }

  return response.json();
}

export async function updateSource(id: number, data: SourceUpdate): Promise<Source> {
  const response = await fetch(`${API_BASE_URL}/api/sources/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to update source");
  }

  return response.json();
}

export async function deleteSource(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sources/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to delete source");
  }
}

export type CrawlTriggerResponse = {
  task_id: string;
  message: string;
  can_crawl: boolean;
};

export async function triggerCrawl(id: number): Promise<CrawlTriggerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/sources/${id}/crawl`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to trigger crawl");
  }

  return response.json();
}

export type CompanyType = {
  id: number;
  name: string;
  slug: string;
  enabled: boolean;
};

export type CompanyTypeCreate = {
  name: string;
};

export type CompanyTypeUpdate = {
  name?: string;
  enabled?: boolean;
};

export async function fetchCompanyTypes(enabled?: boolean): Promise<CompanyType[]> {
  let url = `${API_BASE_URL}/api/company-types`;
  if (enabled !== undefined) {
    url += `?enabled=${enabled}`;
  }
  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch company types");
  }

  return response.json();
}

export async function fetchCompanyType(id: number): Promise<CompanyType> {
  const response = await fetch(`${API_BASE_URL}/api/company-types/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch company type");
  }

  return response.json();
}

export async function createCompanyType(data: CompanyTypeCreate): Promise<CompanyType> {
  const response = await fetch(`${API_BASE_URL}/api/company-types`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to create company type");
  }

  return response.json();
}

export async function updateCompanyType(id: number, data: CompanyTypeUpdate): Promise<CompanyType> {
  const response = await fetch(`${API_BASE_URL}/api/company-types/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to update company type");
  }

  return response.json();
}

export type SourceType = {
  id: number;
  name: string;
  slug: string;
  enabled: boolean;
};

export type SourceTypeCreate = {
  name: string;
};

export type SourceTypeUpdate = {
  name?: string;
  enabled?: boolean;
};

export async function fetchSourceTypes(enabled?: boolean): Promise<SourceType[]> {
  let url = `${API_BASE_URL}/api/source-types`;
  if (enabled !== undefined) {
    url += `?enabled=${enabled}`;
  }
  const response = await fetch(url, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch source types");
  }

  return response.json();
}

export async function fetchSourceType(id: number): Promise<SourceType> {
  const response = await fetch(`${API_BASE_URL}/api/source-types/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch source type");
  }

  return response.json();
}

export async function createSourceType(data: SourceTypeCreate): Promise<SourceType> {
  const response = await fetch(`${API_BASE_URL}/api/source-types`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to create source type");
  }

  return response.json();
}

export async function updateSourceType(id: number, data: SourceTypeUpdate): Promise<SourceType> {
  const response = await fetch(`${API_BASE_URL}/api/source-types/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to update source type");
  }

  return response.json();
}
