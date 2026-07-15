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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { UploadCloud, FileType, Calendar } from "lucide-react";
import { useUploadDocument, useParseDocument } from "../hooks/use-documents";

interface DocumentUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  // If provided, the modal is scoped to this company and the company select field is hidden
  companyId?: string; 
  // If not provided, we need a list of available companies to select from
  companies?: { id: string; name: string }[];
}

export function DocumentUploadModal({ open, onOpenChange, companyId, companies }: DocumentUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("10-K");
  const [fiscalPeriod, setFiscalPeriod] = useState("");
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(companyId || "");

  const uploadMutation = useUploadDocument();
  const parseMutation = useParseDocument();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || !selectedCompanyId || !docType || !fiscalPeriod) return;

    try {
      const doc = await uploadMutation.mutateAsync({
        company_id: selectedCompanyId,
        doc_type: docType,
        fiscal_period: fiscalPeriod,
        file,
      });

      // Automatically queue parsing after upload
      await parseMutation.mutateAsync(doc.id);
      
      onOpenChange(false);
      setFile(null);
      setFiscalPeriod("");
    } catch (err) {
      console.error("Upload failed", err);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-background/80 backdrop-blur-2xl">
        <DialogHeader>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload a financial filing for intelligence parsing.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          
          {!companyId && (
            <div className="grid gap-2">
              <Label>Company</Label>
              <Select value={selectedCompanyId} onValueChange={setSelectedCompanyId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a company" />
                </SelectTrigger>
                <SelectContent>
                  {companies?.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="grid gap-2">
            <Label>Document Type</Label>
            <div className="relative">
              <FileType className="absolute w-4 h-4 text-muted-foreground left-3 top-3" />
              <Select value={docType} onValueChange={setDocType}>
                <SelectTrigger className="pl-9">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="10-K">10-K (Annual)</SelectItem>
                  <SelectItem value="10-Q">10-Q (Quarterly)</SelectItem>
                  <SelectItem value="8-K">8-K (Current)</SelectItem>
                  <SelectItem value="EARNINGS_CALL">Earnings Call Transcript</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-2">
            <Label>Fiscal Period</Label>
            <div className="relative">
              <Calendar className="absolute w-4 h-4 text-muted-foreground left-3 top-3" />
              <Input 
                placeholder="e.g. Q1-2026 or FY-2025" 
                className="pl-9" 
                value={fiscalPeriod}
                onChange={(e) => setFiscalPeriod(e.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label>File</Label>
            <div className="flex items-center justify-center w-full">
              <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer border-border/60 hover:bg-muted/50 hover:border-primary/50 transition-colors">
                <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center px-4">
                  <UploadCloud className="w-8 h-8 mb-2 text-muted-foreground" />
                  {file ? (
                    <p className="text-sm font-medium text-primary">{file.name}</p>
                  ) : (
                    <>
                      <p className="mb-1 text-sm font-semibold">Click to upload or drag and drop</p>
                      <p className="text-xs text-muted-foreground">PDF, TXT, or CSV (MAX. 50MB)</p>
                    </>
                  )}
                </div>
                <Input id="dropzone-file" type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.txt,.csv" />
              </label>
            </div>
          </div>

        </div>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleUpload} disabled={!file || !selectedCompanyId || !fiscalPeriod || uploadMutation.isPending}>
            {uploadMutation.isPending ? "Uploading..." : "Upload & Parse"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
