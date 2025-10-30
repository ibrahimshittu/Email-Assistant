"use client";

import { useEffect, useRef, useState } from "react";
import { sseChat } from "@/lib/sse";

export default function ChatPage() {
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => () => esRef.current?.close(), []);

  const ask = async () => {
    setAnswer("");
    setSources([]);
    setLoading(true);
    esRef.current?.close();
    const es = sseChat(q, (ev) => {
      if (ev.event === "sources") {
        setSources(ev.data.sources || []);
      } else if (ev.event === "token") {
        setAnswer((prev) => prev + (ev.data.token || ""));
      } else if (ev.event === "done") {
        setLoading(false);
        es.close();
      }
    });
    esRef.current = es;
  };

  return (
    <main className="space-y-4">
      <h2 className="text-lg font-semibold">Chat</h2>
      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ask about your emails..."
          className="flex-1 rounded-md border px-3 py-2"
        />
        <button
          onClick={ask}
          disabled={loading || !q}
          className="rounded-md bg-black px-3 py-2 text-white hover:bg-gray-800 disabled:opacity-50"
        >
          Ask
        </button>
      </div>
      {answer && (
        <div className="rounded-md bg-white p-4 shadow">
          <div className="prose whitespace-pre-wrap">{answer}</div>
          {sources.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {sources.map((s: any, i: number) => (
                <span
                  key={i}
                  className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-700"
                >
                  {s.subject} • {new Date(s.date).toLocaleDateString()} •{" "}
                  {s.message_id}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}
