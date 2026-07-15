"use client";

import { useState } from "react";
import { LAYOUT_CONFIG } from "@/config/layout";
import { DocumentsTable } from "@/features/documents/components/DocumentsTable";
import { DocumentUploadModal } from "@/features/documents/components/DocumentUploadModal";
import { useDocumentsList } from "@/features/documents/hooks/use-documents";
import { useCompaniesList } from "@/features/companies/hooks/use-companies";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, UploadCloud, SlidersHorizontal } from "lucide-react";
import { useDebounce } from "@/hooks/use-debounce";

export default function DocumentsPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 500);
  const [uploadOpen, setUploadOpen] = useState(false);
  
  // Note: if backend is mocked, this will just return the mock data based on the API client
  const { data: documents, isLoading, isError } = useDocumentsList();
  
  // We fetch companies globally so the Upload Modal can show the company selector
  const { data: companies } = useCompaniesList();

  // Simple client-side search filtering if backend search isn't fully wired
  const filteredDocs = documents?.filter(d => 
    d.doc_type.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
    d.fiscal_period.toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  return (
    <div className="w-full h-full flex flex-col" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documents Pipeline</h1>
          <p className="text-muted-foreground mt-1">
            Manage your financial filings and track AI parsing intelligence.
          </p>
        </div>
        <Button className="shrink-0 gap-2" onClick={() => setUploadOpen(true)}>
          <UploadCloud className="w-4 h-4" />
          Upload Document
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search by document type or fiscal period..." 
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
        <DocumentsTable 
          documents={filteredDocs} 
          isLoading={isLoading} 
          isError={isError}
          onUpload={() => setUploadOpen(true)}
        />
      </div>

      <DocumentUploadModal 
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        companies={companies || []}
      />
    </div>
  );
}
