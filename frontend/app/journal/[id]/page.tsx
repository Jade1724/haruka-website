"use client";

import Link from "next/link";
import { use } from "react";
import { ArrowLeft } from "@phosphor-icons/react/dist/ssr";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { useJournal } from "@/hooks/useJournals";

const markdownComponents: Components = {
  h1: ({ ...props }) => (
    <h2 className="mt-8 mb-3 text-xl font-semibold first:mt-0" {...props} />
  ),
  h2: ({ ...props }) => (
    <h3 className="mt-8 mb-3 text-lg font-semibold first:mt-0" {...props} />
  ),
  h3: ({ ...props }) => (
    <h4 className="mt-6 mb-2 text-base font-semibold first:mt-0" {...props} />
  ),
  p: ({ ...props }) => (
    <p className="text-sm leading-7 text-muted-foreground" {...props} />
  ),
  a: ({ ...props }) => (
    <a
      className="text-foreground underline underline-offset-4 hover:text-muted-foreground"
      target="_blank"
      rel="noopener noreferrer"
      {...props}
    />
  ),
  ul: ({ ...props }) => (
    <ul className="list-disc space-y-1 pl-5 text-sm leading-7 text-muted-foreground" {...props} />
  ),
  ol: ({ ...props }) => (
    <ol className="list-decimal space-y-1 pl-5 text-sm leading-7 text-muted-foreground" {...props} />
  ),
  blockquote: ({ ...props }) => (
    <blockquote
      className="border-l-2 border-border pl-4 text-sm italic text-muted-foreground"
      {...props}
    />
  ),
  hr: ({ ...props }) => <hr className="border-border" {...props} />,
  code: ({ className, ...props }) => (
    <code
      className={`rounded bg-muted px-1.5 py-0.5 font-mono text-xs ${className ?? ""}`}
      {...props}
    />
  ),
  pre: ({ ...props }) => (
    <pre
      className="overflow-x-auto rounded-lg bg-muted p-4 font-mono text-xs"
      {...props}
    />
  ),
  table: ({ ...props }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm" {...props} />
    </div>
  ),
  th: ({ ...props }) => (
    <th
      className="border-b border-border px-3 py-2 text-left font-medium"
      {...props}
    />
  ),
  td: ({ ...props }) => (
    <td className="border-b border-border px-3 py-2 text-muted-foreground" {...props} />
  ),
  img: ({ alt, ...props }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img className="rounded-lg" alt={alt ?? ""} {...props} />
  ),
};

const fmt = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString("en-AU", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

export default function JournalEntryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: entry, isFetching, error } = useJournal(id);

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <Link
        href="/journal"
        className="mb-10 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft size={14} />
        Journal
      </Link>

      {isFetching && !entry && (
        <p className="text-sm text-muted-foreground">Loading…</p>
      )}

      {error && (
        <p className="text-sm text-destructive">
          Failed to load this journal entry.
        </p>
      )}

      {entry && (
        <article>
          <header className="mb-8 flex flex-col gap-2">
            <h1 className="text-2xl font-semibold">{entry.title}</h1>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span>Published {fmt(entry.published_on)}</span>
              {entry.updated_on !== entry.published_on && (
                <span>Updated {fmt(entry.updated_on)}</span>
              )}
            </div>
          </header>

          <div className="flex flex-col gap-4">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {entry.content}
            </ReactMarkdown>
          </div>
        </article>
      )}
    </div>
  );
}
