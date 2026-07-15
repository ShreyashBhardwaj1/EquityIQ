"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PlayCircle, Calendar } from "lucide-react";
import { useGenerateReport } from "../hooks/use-reports";
import { useRouter } from "next/navigation";

interface GenerateReportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  companyId: string;
}

export function GenerateReportDialog({ open, onOpenChange, companyId }: GenerateReportDialogProps) {
  const [fiscalPeriod, setFiscalPeriod] = useState("");
  const generateMutation = useGenerateReport();
  const router = useRouter();

  const handleGenerate = async () => {
    if (!companyId || !fiscalPeriod) return;

    try {
      const summary = await generateMutation.mutateAsync({
        company_id: companyId,
        fiscal_period: fiscalPeriod,
      });

      onOpenChange(false);
      setFiscalPeriod("");
      
      // Navigate to the streaming viewer
      router.push(`/companies/${companyId}/reports/${summary.id}`);
    } catch (err) {
      console.error("Failed to generate report", err);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-background/80 backdrop-blur-2xl">
        <DialogHeader>
          <DialogTitle>Generate Report</DialogTitle>
          <DialogDescription>
            Synthesize parsed intelligence into a comprehensive financial report.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Target Fiscal Period</Label>
            <div className="relative">
              <Calendar className="absolute w-4 h-4 text-muted-foreground left-3 top-3" />
              <Input 
                placeholder="e.g. Q1-2026 or FY-2025" 
                className="pl-9" 
                value={fiscalPeriod}
                onChange={(e) => setFiscalPeriod(e.target.value)}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Ensure you have parsed documents for this fiscal period before generating.
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleGenerate} disabled={!fiscalPeriod || generateMutation.isPending} className="gap-2">
            <PlayCircle className="w-4 h-4" />
            {generateMutation.isPending ? "Starting..." : "Generate"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
