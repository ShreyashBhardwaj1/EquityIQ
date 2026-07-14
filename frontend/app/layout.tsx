import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/providers/providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "EquityIQ — AI-Powered Financial Intelligence",
    template: "%s | EquityIQ",
  },
  description:
    "EquityIQ is an AI-powered financial intelligence platform that helps analysts research companies, analyze financials, and generate investment insights at scale.",
  keywords: [
    "financial intelligence",
    "AI finance",
    "equity research",
    "financial analysis",
    "investment platform",
  ],
  authors: [{ name: "EquityIQ" }],
  creator: "EquityIQ",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f1f5f9" },
    { media: "(prefers-color-scheme: dark)", color: "#0c1322" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className={inter.variable}>
      <body className="min-h-screen font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
