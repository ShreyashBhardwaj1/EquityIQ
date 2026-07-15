"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ReportSummary } from "../types";
import { FileText, Download, PlayCircle, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface ReportsTableProps {
  reports: ReportSummary[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onGenerate?: () => void;
}

export function ReportsTable({ reports, isLoading, isError, onGenerate }: ReportsTableProps) {
  const router = useRouter();

  if (isError) {
    return (
      <div className="p-8 text-center border rounded-lg bg-destructive/10 text-destructive border-destructive/20">
        Failed to load reports. Please try again.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="w-full h-16 rounded-md" />
        ))}
      </div>
    );
  }

  if (!reports || reports.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-background/50">
        <div className="flex items-center justify-center w-16 h-16 mb-4 rounded-full bg-primary/10">
          <FileText className="w-8 h-8 text-primary" />
        </div>
        <h3 className="mb-2 text-lg font-semibold">No Reports Generated</h3>
        <p className="mb-6 text-sm text-muted-foreground max-w-sm">
          Select a fiscal period to synthesize the parsed intelligence into a comprehensive financial report.
        </p>
        {onGenerate && (
          <Button onClick={onGenerate} className="gap-2">
            <PlayCircle className="w-4 h-4" />
            Generate Report
          </Button>
        )}
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    if (status === "COMPLETED") return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
    if (status === "FAILED") return <XCircle className="w-4 h-4 text-destructive" />;
    return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
  };

  return (
    <div className="border rounded-md bg-background/50 backdrop-blur-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Fiscal Period</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Generated At</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {reports.map((report) => (
            <TableRow 
              key={report.id} 
              className="cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => router.push(`/companies/${report.company_id}/reports/${report.id}`)}
            >
              <TableCell className="font-medium">
                <Badge variant="outline" className="font-mono">{report.fiscal_period}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  {getStatusIcon(report.status)}
                  <span className="capitalize">{report.status.toLowerCase()}</span>
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {report.generation_duration ? `${report.generation_duration}s` : "-"}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {new Date(report.created_at).toLocaleString()}
              </TableCell>
              <TableCell className="text-right">
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Just download Markdown for MVP
                    window.location.href = `${process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}/companies/${report.company_id}/reports/${report.id}/download?fmt=markdown`;
                  }}
                  disabled={report.status !== "COMPLETED"}
                  className="gap-2"
                >
                  <Download className="w-4 h-4" />
                  <span className="sr-only sm:not-sr-only">Download</span>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
