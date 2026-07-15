"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { LAYOUT_CONFIG } from "@/config/layout";
import { ReportsTable } from "@/features/reports/components/ReportsTable";
import { GenerateReportDialog } from "@/features/reports/components/GenerateReportDialog";
import { useReportsList } from "@/features/reports/hooks/use-reports";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, PlayCircle, SlidersHorizontal, ChevronLeft } from "lucide-react";
import { useDebounce } from "@/hooks/use-debounce";

export default function CompanyReportsPage() {
  const params = useParams();
  const router = useRouter();
  const companyId = params.id as string;

  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 500);
  const [generateOpen, setGenerateOpen] = useState(false);
  
  const { data: reports, isLoading, isError } = useReportsList(companyId);

  const filteredReports = reports?.filter(r => 
    r.title?.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
    r.fiscal_period.toLowerCase().includes(debouncedSearch.toLowerCase())
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
            <h1 className="text-3xl font-bold tracking-tight">Company Reports</h1>
            <p className="text-muted-foreground mt-1">
              Generate and review comprehensive financial narratives for this company.
            </p>
          </div>
        </div>
        <Button className="shrink-0 gap-2" onClick={() => setGenerateOpen(true)}>
          <PlayCircle className="w-4 h-4" />
          Generate Report
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search reports by title or period..." 
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
        <ReportsTable 
          reports={filteredReports} 
          isLoading={isLoading} 
          isError={isError}
          onGenerate={() => setGenerateOpen(true)}
        />
      </div>

      <GenerateReportDialog 
        open={generateOpen}
        onOpenChange={setGenerateOpen}
        companyId={companyId}
      />
    </div>
  );
}
