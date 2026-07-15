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
import { Progress } from "@/components/ui/progress";
import { Document } from "../types";
import { DocumentStatusBadge } from "./DocumentStatusBadge";
import { FileText, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DocumentsTableProps {
  documents: Document[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onUpload?: () => void;
}

export function DocumentsTable({ documents, isLoading, isError, onUpload }: DocumentsTableProps) {
  if (isError) {
    return (
      <div className="p-8 text-center border rounded-lg bg-destructive/10 text-destructive border-destructive/20">
        Failed to load documents. Please try again.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="w-full h-16 rounded-md" />
        ))}
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-background/50">
        <div className="flex items-center justify-center w-16 h-16 mb-4 rounded-full bg-primary/10">
          <FileText className="w-8 h-8 text-primary" />
        </div>
        <h3 className="mb-2 text-lg font-semibold">No Documents Found</h3>
        <p className="mb-6 text-sm text-muted-foreground max-w-sm">
          Upload financial filings to begin parsing and extracting financial intelligence.
        </p>
        {onUpload && (
          <Button onClick={onUpload} className="gap-2">
            <UploadCloud className="w-4 h-4" />
            Upload Document
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="border rounded-md bg-background/50 backdrop-blur-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Document Type</TableHead>
            <TableHead>Fiscal Period</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Intelligence Confidence</TableHead>
            <TableHead className="text-right">Uploaded</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id} className="cursor-pointer hover:bg-muted/50">
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  {doc.doc_type}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant="outline" className="font-mono">{doc.fiscal_period}</Badge>
              </TableCell>
              <TableCell>
                <DocumentStatusBadge status={doc.parsing_status} />
              </TableCell>
              <TableCell>
                {doc.parsing_status === "COMPLETED" ? (
                  <div className="flex items-center gap-2">
                    <Progress value={doc.parsing_confidence * 100} className="w-24 h-2" />
                    <span className="text-xs text-muted-foreground">
                      {(doc.parsing_confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ) : (
                  <span className="text-xs text-muted-foreground italic">Pending</span>
                )}
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-sm">
                {new Date(doc.created_at).toLocaleDateString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
