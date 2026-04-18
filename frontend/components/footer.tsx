"use client";

import { useState } from "react";
import Link from "next/link";
import { GithubLogo } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const inputClass =
  "w-full rounded-sm border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring";

export default function Footer() {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // TODO: wire up to backend contact endpoint
    setSubmitted(true);
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
              <input
                type="text"
                placeholder="Name"
                required
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className={inputClass}
              />
              <input
                type="email"
                placeholder="Email"
                required
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                className={inputClass}
              />
              <textarea
                placeholder="Message"
                required
                rows={4}
                value={form.message}
                onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
                className={cn(inputClass, "resize-none")}
              />
              <Button type="submit" className="self-start">
                Send
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
