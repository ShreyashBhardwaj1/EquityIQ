import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";

export function DocumentStatusBadge({ status }: { status: string }) {
  switch (status) {
    case "PENDING":
      return (
        <Badge variant="outline" className="gap-1.5 text-muted-foreground">
          <Clock className="w-3 h-3" />
          Pending
        </Badge>
      );
    case "PARSING":
      return (
        <Badge variant="secondary" className="gap-1.5 text-blue-600 bg-blue-500/10 hover:bg-blue-500/20">
          <Loader2 className="w-3 h-3 animate-spin" />
          Parsing
        </Badge>
      );
    case "COMPLETED":
      return (
        <Badge variant="secondary" className="gap-1.5 text-emerald-600 bg-emerald-500/10 hover:bg-emerald-500/20">
          <CheckCircle2 className="w-3 h-3" />
          Completed
        </Badge>
      );
    case "FAILED":
      return (
        <Badge variant="destructive" className="gap-1.5">
          <XCircle className="w-3 h-3" />
          Failed
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}
