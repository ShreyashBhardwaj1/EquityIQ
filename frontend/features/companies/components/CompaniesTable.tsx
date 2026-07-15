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
import { Company } from "../types";
import { CompaniesEmptyState } from "./CompaniesEmptyState";

interface CompaniesTableProps {
  companies: Company[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onAddCompany?: () => void;
}

export function CompaniesTable({ companies, isLoading, isError, onAddCompany }: CompaniesTableProps) {
  if (isError) {
    return (
      <div className="p-8 text-center border rounded-lg bg-destructive/10 text-destructive border-destructive/20">
        Failed to load companies. Please try again.
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

  if (!companies || companies.length === 0) {
    return <CompaniesEmptyState onAdd={onAddCompany} />;
  }

  return (
    <div className="border rounded-md bg-background/50 backdrop-blur-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Company</TableHead>
            <TableHead>Ticker</TableHead>
            <TableHead>Sector</TableHead>
            <TableHead>Industry</TableHead>
            <TableHead>Country</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {companies.map((company) => (
            <TableRow key={company.id} className="cursor-pointer hover:bg-muted/50">
              <TableCell className="font-medium">{company.name}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono">{company.ticker}</Badge>
                  <span className="text-xs text-muted-foreground">{company.exchange}</span>
                </div>
              </TableCell>
              <TableCell>{company.sector}</TableCell>
              <TableCell>{company.industry}</TableCell>
              <TableCell>{company.country}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
