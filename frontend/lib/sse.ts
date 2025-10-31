import type { ChatSource } from "./api";

const BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

export interface SSEEvent {
  event: "sources" | "token" | "done" | "error";
  data: {
    sources?: ChatSource[];
    token?: string;
    error?: string;
  };
}

export async function streamChat(
  question: string,
  options: {
    top_k?: number;
    temperature?: number;
    max_tokens?: number;
  },
  onEvent: (evt: SSEEvent) => void
): Promise<void> {
  const response = await fetch(`${BACKEND}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      top_k: options.top_k ?? 6,
      temperature: options.temperature,
      max_tokens: options.max_tokens,
    }),
  });

  if (!response.ok) {
    throw new Error(`Stream failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error("No response body");
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.slice(6));
            onEvent(data);
          } catch (e) {
            console.error("Failed to parse SSE data:", e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
