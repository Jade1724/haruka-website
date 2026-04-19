import { useQuery } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type JournalSummary = {
  id: string;
  title: string;
  published_on: string;
  updated_on: string;
};

export type JournalDetail = JournalSummary & {
  content: string;
};

async function fetchJournals(): Promise<JournalSummary[]> {
  const res = await fetch(`${API_BASE}/journals`);
  if (!res.ok) throw new Error(`Failed to fetch journals: ${res.status}`);
  return res.json();
}

async function fetchJournal(id: string): Promise<JournalDetail> {
  const res = await fetch(`${API_BASE}/journals/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch journal: ${res.status}`);
  return res.json();
}

export function useJournals() {
  const { data, isFetching, error } = useQuery({
    queryKey: ["journals"],
    queryFn: fetchJournals,
  });

  return { data, isFetching, error };
}

export function useJournal(id: string) {
  const { data, isFetching, error } = useQuery({
    queryKey: ["journals", id],
    queryFn: () => fetchJournal(id),
    enabled: Boolean(id),
  });

  return { data, isFetching, error };
}
