"use client";

import { useParams, useRouter } from "next/navigation";
import { LAYOUT_CONFIG } from "@/config/layout";
import { ReportStreamingConsole } from "@/features/reports/components/ReportStreamingConsole";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";

export default function ReportViewerPage() {
  const params = useParams();
  const router = useRouter();
  
  const companyId = params.id as string;
  const reportId = params.reportId as string;

  return (
    <div className="w-full h-full flex flex-col" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => router.back()}
          className="shrink-0"
        >
          <ChevronLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Report Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Synthesizing and streaming financial narrative.
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <ReportStreamingConsole 
          companyId={companyId} 
          reportId={reportId} 
          onFinish={() => router.push(`/reports`)}
        />
      </div>

    </div>
  );
}
