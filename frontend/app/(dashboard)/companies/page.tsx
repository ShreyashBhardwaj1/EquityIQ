"use client";

import { useState } from "react";
import { LAYOUT_CONFIG } from "@/config/layout";
import { CompaniesTable } from "@/features/companies/components/CompaniesTable";
import { useCompaniesList } from "@/features/companies/hooks/use-companies";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, SlidersHorizontal } from "lucide-react";
import { useDebounce } from "@/hooks/use-debounce"; // We need to create this

export default function CompaniesPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 500);
  
  // Connect to React Query
  // Note: if backend is mocked, this will just return the mock data based on the API client
  const { data: companies, isLoading, isError } = useCompaniesList({
    // Optional filters can be passed here
  });

  // Simple client-side search filtering if backend search isn't fully wired,
  // or you could use useCompaniesSearch(debouncedSearch) if the API supports it cleanly.
  // For now, we'll do client side filtering over the list to make it robust against mocks.
  const filteredCompanies = companies?.filter(c => 
    c.name.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
    c.ticker.toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  return (
    <div className="w-full h-full flex flex-col" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Companies</h1>
          <p className="text-muted-foreground mt-1">
            Manage your universe of active companies and track their financial data.
          </p>
        </div>
        <Button className="shrink-0 gap-2">
          <Plus className="w-4 h-4" />
          Add Company
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search companies by name or ticker..." 
            className="pl-9 bg-background/50 backdrop-blur-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="outline" className="gap-2 bg-background/50 backdrop-blur-sm">
          <SlidersHorizontal className="w-4 h-4" />
          Filters
        </Button>
      </div>

      {/* Table Content */}
      <div className="flex-1">
        <CompaniesTable 
          companies={filteredCompanies} 
          isLoading={isLoading} 
          isError={isError}
          onAddCompany={() => {}}
        />
      </div>

    </div>
  );
}
