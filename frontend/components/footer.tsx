"use client";

import { useState } from "react";
import Link from "next/link";
import { GithubLogo } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupTextarea,
  InputGroupText,
} from "@/components/ui/input-group";

export default function Footer() {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}/contact`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        }
      );
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <footer className="mt-auto border-t border-border">
      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-12 px-6 py-12 sm:grid-cols-2">
        <div>
          <h2 className="mb-4 text-sm font-semibold">Get in touch</h2>
          {submitted ? (
            <p className="text-sm text-muted-foreground">
              Thanks — I&apos;ll get back to you soon.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <InputGroup>
                <InputGroupAddon align="block-start">
                  <InputGroupText>Name</InputGroupText>
                </InputGroupAddon>
                <InputGroupInput
                  type="text"
                  required
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                />
              </InputGroup>

              <InputGroup>
                <InputGroupAddon align="block-start">
                  <InputGroupText>Email</InputGroupText>
                </InputGroupAddon>
                <InputGroupInput
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                />
              </InputGroup>

              <InputGroup>
                <InputGroupAddon align="block-start">
                  <InputGroupText>Message</InputGroupText>
                </InputGroupAddon>
                <InputGroupTextarea
                  required
                  rows={4}
                  value={form.message}
                  onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
                />
              </InputGroup>

              {error && (
                <p className="text-xs text-destructive">{error}</p>
              )}

              <Button type="submit" disabled={loading} className="self-start">
                {loading ? "Sending…" : "Send"}
              </Button>
            </form>
          )}
        </div>

        <div>
          <h2 className="mb-4 text-sm font-semibold">Links</h2>
          <Link
            href="https://github.com/Jade1724"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <GithubLogo size={18} />
            GitHub
          </Link>
        </div>
      </div>
    </footer>
  );
}
