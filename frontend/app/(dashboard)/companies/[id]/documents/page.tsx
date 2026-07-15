"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { LAYOUT_CONFIG } from "@/config/layout";
import { DocumentsTable } from "@/features/documents/components/DocumentsTable";
import { DocumentUploadModal } from "@/features/documents/components/DocumentUploadModal";
import { useDocumentsList } from "@/features/documents/hooks/use-documents";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, UploadCloud, SlidersHorizontal, ChevronLeft } from "lucide-react";
import { useDebounce } from "@/hooks/use-debounce";

export default function CompanyDocumentsPage() {
  const params = useParams();
  const router = useRouter();
  const companyId = params.id as string;

  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 500);
  const [uploadOpen, setUploadOpen] = useState(false);
  
  const { data: documents, isLoading, isError } = useDocumentsList(companyId);
  
  const filteredDocs = documents?.filter(d => 
    d.doc_type.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
    d.fiscal_period.toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  return (
    <div className="w-full h-full flex flex-col" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => router.back()}
            className="shrink-0"
          >
            <ChevronLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Company Documents</h1>
            <p className="text-muted-foreground mt-1">
              Manage financial filings specifically for this company.
            </p>
          </div>
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
        companyId={companyId}
      />
    </div>
  );
}
