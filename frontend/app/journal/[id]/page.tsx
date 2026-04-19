import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "@phosphor-icons/react/dist/ssr";
import { journals } from "../data";

export function generateStaticParams() {
  return journals.map((entry) => ({ id: entry.id }));
}

export default async function JournalEntryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const entry = journals.find((j) => j.id === id);

  if (!entry) notFound();

  const paragraphs = entry.content
    .split(/\n\n+/)
    .map((p) => p.trim())
    .filter(Boolean);

  const fmt = (date: Date) =>
    date.toLocaleDateString("en-AU", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <Link
        href="/journal"
        className="mb-10 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft size={14} />
        Journal
      </Link>

      <article>
        <header className="mb-8 flex flex-col gap-2">
          <h1 className="text-2xl font-semibold">{entry.title}</h1>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <span>Published {fmt(entry.publishedOn)}</span>
            {entry.updatedOn.getTime() !== entry.publishedOn.getTime() && (
              <span>Updated {fmt(entry.updatedOn)}</span>
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
    </div>
  );
}
