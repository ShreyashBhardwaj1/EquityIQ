"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { Toaster } from "sonner";
import { useState } from "react";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        attribute="class"
        defaultTheme="dark"
        enableSystem={false}
        disableTransitionOnChange={false}
      >
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            classNames: {
              toast:
                "font-sans text-sm border border-border bg-card text-card-foreground shadow-card",
              success: "border-green-500/30 [&>[data-icon]]:text-green-500",
              error: "border-destructive/30 [&>[data-icon]]:text-destructive",
            },
          }}
          richColors
        />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
