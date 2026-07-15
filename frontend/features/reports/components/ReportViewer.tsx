"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";

interface ReportViewerProps {
  content: string;
}

export function ReportViewer({ content }: ReportViewerProps) {
  return (
    <div className="w-full h-full p-6 lg:p-10 mx-auto max-w-4xl bg-background/50 backdrop-blur-xl border rounded-lg shadow-sm">
      <article className="prose prose-sm md:prose-base dark:prose-invert prose-headings:font-bold prose-a:text-primary max-w-none prose-table:border-collapse prose-th:border prose-td:border prose-th:bg-muted/50">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSanitize]}
        >
          {content}
        </ReactMarkdown>
      </article>
    </div>
  );
}
