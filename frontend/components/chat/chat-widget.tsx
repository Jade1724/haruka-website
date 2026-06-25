"use client";

import { useEffect, useRef, useState } from "react";
import { ChatCircle, PaperPlaneRight, Robot, X } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { ChatMessageBubble } from "./chat-message";
import { useChat } from "./use-chat";

const SUGGESTIONS = [
  "Does Haruka have a project building a VR game?",
  "What has Haruka written about setting up Next.js with FastAPI?",
  "Where can I see Haruka's work history?",
];

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, isStreaming, sendMessage } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  function submit(text: string) {
    sendMessage(text);
    setInput("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    submit(input);
  }

  if (!open) {
    return (
      <Button
        size="icon-lg"
        onClick={() => setOpen(true)}
        aria-label="Chat with mecha-haruka"
        className="fixed right-5 bottom-5 z-50 shadow-lg"
      >
        <ChatCircle size={20} weight="fill" />
      </Button>
    );
  }

  return (
    <div className="fixed right-5 bottom-5 z-50 flex h-[70vh] max-h-[560px] w-[min(360px,calc(100vw-2.5rem))] flex-col border border-border bg-background shadow-xl">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <div className="flex items-center gap-2">
          <Robot size={16} weight="fill" className="text-primary" />
          <div className="leading-tight">
            <p className="text-xs font-semibold">mecha-haruka</p>
            <p className="text-[10px] text-muted-foreground">AI persona of Haruka</p>
          </div>
        </div>
        <Button
          size="icon-xs"
          variant="ghost"
          onClick={() => setOpen(false)}
          aria-label="Close chat"
        >
          <X size={14} />
        </Button>
      </div>

      <div ref={scrollRef} className="flex flex-1 flex-col gap-3 overflow-y-auto p-3">
        {messages.length === 0 ? (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-muted-foreground">
              Ask about Haruka&apos;s projects, experience, or dev journal.
            </p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => submit(s)}
                className="border border-border bg-muted/40 px-2.5 py-1.5 text-left text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        ) : (
          messages.map((m, i) => <ChatMessageBubble key={i} message={m} />)
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-border p-2">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about Haruka…"
            disabled={isStreaming}
            className="h-8 flex-1 border border-border bg-background px-2.5 text-xs outline-none focus-visible:border-ring disabled:opacity-50"
          />
          <Button
            type="submit"
            size="icon"
            disabled={isStreaming || !input.trim()}
            aria-label="Send message"
          >
            <PaperPlaneRight size={15} weight="fill" />
          </Button>
        </div>
        <p className="mt-1.5 text-[10px] text-muted-foreground">
          Replies are AI-generated via Azure OpenAI. Don&apos;t share sensitive info.
        </p>
      </form>
    </div>
  );
}
