"use client";

import Link from "next/link";
import { useJournals } from "@/hooks/useJournals";

export default function JournalPage() {
  const { data: journals, isFetching, error } = useJournals();

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="mb-12 text-2xl font-semibold">Journal</h1>

      {isFetching && !journals && (
        <p className="text-sm text-muted-foreground">Loading journals…</p>
      )}

      {error && (
        <p className="text-sm text-destructive">
          Failed to load journals. Is the backend running?
        </p>
      )}

      {journals && (
        <ul className="flex flex-col divide-y divide-border">
          {journals.map((entry) => (
            <li key={entry.id}>
              <Link
                href={`/journal/${entry.id}`}
                className="group flex flex-col gap-1 py-5"
              >
                <span className="font-medium group-hover:underline underline-offset-4">
                  {entry.title}
                </span>
                <span className="text-xs text-muted-foreground">
                  {new Date(entry.published_on).toLocaleDateString("en-AU", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
