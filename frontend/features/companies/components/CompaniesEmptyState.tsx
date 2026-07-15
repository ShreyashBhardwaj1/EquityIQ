import { Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CompaniesEmptyState({ onAdd }: { onAdd?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-background/50">
      <div className="flex items-center justify-center w-16 h-16 mb-4 rounded-full bg-primary/10">
        <Building2 className="w-8 h-8 text-primary" />
      </div>
      <h3 className="mb-2 text-lg font-semibold">No Companies Found</h3>
      <p className="mb-6 text-sm text-muted-foreground max-w-sm">
        You haven&apos;t added any companies to your workspace yet. Add a company to start analyzing financial data.
      </p>
      {onAdd && (
        <Button onClick={onAdd}>
          Add Company
        </Button>
      )}
    </div>
  );
}
