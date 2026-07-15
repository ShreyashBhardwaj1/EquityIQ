import { useState, useEffect, useRef } from "react";
import { StreamingReportState } from "../types";
import { getAuthHeaders } from "@/lib/api-client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export function useReportStream(companyId: string, reportId: string) {
  const [state, setState] = useState<StreamingReportState>({
    status: "idle",
    progressPercentage: 0,
    message: "Initializing connection...",
    content: "",
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!companyId || !reportId) return;

    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    const connectToStream = async () => {
      try {
        setState(s => ({ ...s, status: "queued", message: "Connecting to stream..." }));
        
        const response = await fetch(`${API_BASE_URL}/companies/${companyId}/reports/${reportId}/stream`, {
          method: "GET",
          headers: getAuthHeaders(),
          signal,
        });

        if (!response.ok) {
          throw new Error(`Failed to connect: ${response.statusText}`);
        }
        if (!response.body) {
          throw new Error("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          
          let eolIndex;
          while ((eolIndex = buffer.indexOf("\n\n")) >= 0) {
            const chunk = buffer.slice(0, eolIndex).trim();
            buffer = buffer.slice(eolIndex + 2);
            
            if (!chunk) continue;
            if (chunk.startsWith(":")) continue; // SSE heartbeat comment

            const lines = chunk.split("\n");
            let eventType = "message";
            let dataStr = "";
            
            for (const line of lines) {
              if (line.startsWith("event:")) {
                eventType = line.slice(6).trim();
              } else if (line.startsWith("data:")) {
                dataStr = line.slice(5).trim();
              }
            }

            if (!dataStr) continue;

            let data;
            try {
              data = JSON.parse(dataStr);
            } catch (e) {
              console.error("Failed to parse SSE JSON:", dataStr);
              continue;
            }

            setState((prev) => {
              const next = { ...prev };

              switch (eventType) {
                case "queued":
                  next.status = "queued";
                  next.message = "Report generation queued...";
                  break;
                case "progress":
                  next.status = "progress";
                  next.progressPercentage = data.percentage || 0;
                  next.message = data.status || "In progress...";
                  break;
                case "section_started":
                  next.status = "streaming";
                  next.message = `Generating section: ${data.section_name}`;
                  break;
                case "token":
                  next.status = "streaming";
                  next.content += data.text;
                  break;
                case "section_completed":
                  next.status = "streaming";
                  break;
                case "completed":
                  next.status = "completed";
                  next.progressPercentage = 100;
                  next.message = "Report complete!";
                  break;
                case "failed":
                  next.status = "failed";
                  next.message = data.error || "Generation failed.";
                  break;
              }
              
              return next;
            });

            if (eventType === "completed" || eventType === "failed") {
              return; // Terminate reading
            }
          }
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("Streaming error:", err);
          setState(s => ({ ...s, status: "failed", message: err.message || "Connection lost." }));
        }
      }
    };

    connectToStream();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [companyId, reportId]);

  return state;
}
