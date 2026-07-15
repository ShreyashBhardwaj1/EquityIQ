"use client";

import { useState } from "react";
import { LAYOUT_CONFIG } from "@/config/layout";
import { ReportsTable } from "@/features/reports/components/ReportsTable";
import { GenerateReportDialog } from "@/features/reports/components/GenerateReportDialog";
import { useCompaniesList } from "@/features/companies/hooks/use-companies";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, PlayCircle, SlidersHorizontal } from "lucide-react";
import { useDebounce } from "@/hooks/use-debounce";
import { ReportSummary } from "@/features/reports/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";

export default function ReportsPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 500);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>("");

  // Since we don't have a global reports endpoint yet, we require the user to pick a company 
  // via a UI filter dropdown first, OR we fetch companies and use a mock list. 
  // For the architecture to stay intact, we'll fetch companies and simulate a global list if needed, 
  // or simply prompt them to select a company in the UI to fetch reports for that company.
  
  const { data: companies } = useCompaniesList();
  
  // Real endpoint expects a companyId. If none selected, we can't fetch.
  // We'll require company selection to view reports since the backend is scoped.
  // When a global endpoint is added, we just swap the hook to useGlobalReportsList().
  
  // To avoid breaking React Query rules, we'll just not fetch if no company is selected,
  // but we'll mock an empty array or loading state.
  const [mockReports, setMockReports] = useState<ReportSummary[]>([]);

  // Simple client-side search filtering
  const filteredReports = mockReports?.filter(r => 
    r.title?.toLowerCase().includes(debouncedSearch.toLowerCase()) || 
    r.fiscal_period.toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  return (
    <div className="w-full h-full flex flex-col" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Intelligence Reports</h1>
          <p className="text-muted-foreground mt-1">
            Generate and review comprehensive financial narratives synthesized by EquityIQ.
          </p>
        </div>
        <Button className="shrink-0 gap-2" onClick={() => setGenerateOpen(true)} disabled={!selectedCompanyId}>
          <PlayCircle className="w-4 h-4" />
          Generate Report
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="w-64">
          <Select value={selectedCompanyId} onValueChange={setSelectedCompanyId}>
            <SelectTrigger className="bg-background/50 backdrop-blur-sm">
              <SelectValue placeholder="Select Company Scope..." />
            </SelectTrigger>
            <SelectContent>
              {companies?.map((c) => (
                <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
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
        {!selectedCompanyId ? (
          <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-background/50">
            <h3 className="mb-2 text-lg font-semibold">Select a Company</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Please select a company from the dropdown above to view or generate its intelligence reports.
            </p>
          </div>
        ) : (
          <ReportsTable 
            reports={filteredReports} 
            isLoading={false} 
            isError={false}
            onGenerate={() => setGenerateOpen(true)}
          />
        )}
      </div>

      <GenerateReportDialog 
        open={generateOpen}
        onOpenChange={setGenerateOpen}
        companyId={selectedCompanyId}
      />
    </div>
  );
}
