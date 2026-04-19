"use client";

import Link from "next/link";
import { use } from "react";
import { ArrowLeft } from "@phosphor-icons/react/dist/ssr";
import { useJournal } from "@/hooks/useJournals";

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

  const paragraphs = entry?.content
    .split(/\n\n+/)
    .map((p) => p.trim())
    .filter(Boolean) ?? [];

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
            {paragraphs.map((para, i) => (
              <p key={i} className="text-sm leading-7 text-muted-foreground">
                {para}
              </p>
            ))}
          </div>
        </article>
      )}
    </div>
  );
}
