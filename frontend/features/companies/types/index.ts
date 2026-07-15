export interface Company {
  id: string;
  workspace_id: string;
  ticker: string;
  exchange: string;
  name: string;
  sector: string;
  industry: string;
  country: string;
  fiscal_year_end: string;
  currency: string;
}

export interface CompaniesListParams {
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  exchange?: string;
  sector?: string;
  industry?: string;
  country?: string;
}

export interface CompanyCreatePayload {
  ticker: string;
  exchange: string;
  name: string;
  sector: string;
  industry: string;
  country: string;
  fiscal_year_end: string;
  currency: string;
}
