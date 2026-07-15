"use client";

import { useReportStream } from "../hooks/use-report-stream";
import { ReportViewer } from "./ReportViewer";
import { Progress } from "@/components/ui/progress";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface ReportStreamingConsoleProps {
  companyId: string;
  reportId: string;
  onFinish?: () => void;
}

export function ReportStreamingConsole({ companyId, reportId, onFinish }: ReportStreamingConsoleProps) {
  const state = useReportStream(companyId, reportId);

  if (state.status === "failed") {
    return (
      <div className="w-full max-w-2xl mx-auto mt-12">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Generation Failed</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  const isGenerating = state.status === "queued" || state.status === "progress";

  return (
    <div className="flex flex-col w-full h-full space-y-6">
      
      {/* Status Bar */}
      <div className="flex flex-col p-4 bg-background/50 backdrop-blur-sm border rounded-lg shadow-sm gap-3">
        <div className="flex justify-between items-center text-sm">
          <div className="flex items-center gap-2 font-medium">
            {isGenerating ? (
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
            ) : state.status === "completed" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            ) : (
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            )}
            <span>{state.message}</span>
          </div>
          <div className="text-muted-foreground font-mono">
            {state.progressPercentage.toFixed(0)}%
          </div>
        </div>
        
        <Progress value={state.progressPercentage} className="h-1.5" />
      </div>

      {/* Content Viewer */}
      {(state.status === "streaming" || state.status === "completed") && (
        <div className="flex-1 overflow-y-auto min-h-[500px]">
          <ReportViewer content={state.content} />
          
          {state.status === "streaming" && (
            <div className="flex items-center justify-center py-6 text-muted-foreground text-sm gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Writing report...
            </div>
          )}
          
          {state.status === "completed" && onFinish && (
            <div className="flex justify-center pt-6 pb-12">
              <Button onClick={onFinish} variant="default">
                Return to Directory
              </Button>
            </div>
          )}
        </div>
      )}
      
      {isGenerating && (
        <div className="flex flex-col items-center justify-center flex-1 min-h-[400px] border rounded-lg border-dashed bg-background/30 text-center px-4">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Analyzing Intelligence</h3>
          <p className="text-muted-foreground max-w-md">
            EquityIQ is synthesizing the financial foundation and cross-referencing semantic chunks to build your report. This usually takes 10-30 seconds.
          </p>
        </div>
      )}

    </div>
  );
}
