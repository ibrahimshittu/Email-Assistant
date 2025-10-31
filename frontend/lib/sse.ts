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
    let buffer = "";
    let currentEvent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          // Empty line resets the event
          currentEvent = "";
          continue;
        }

        if (trimmed.startsWith("event:")) {
          currentEvent = trimmed.substring(6).trim();
        } else if (trimmed.startsWith("data:")) {
          const dataStr = trimmed.substring(5).trim();

          if (!dataStr || !currentEvent) continue;

          try {
            const data = JSON.parse(dataStr);

            onEvent({
              event: currentEvent as "sources" | "token" | "done" | "error",
              data,
            });
          } catch (e) {
            console.error("Failed to parse SSE data:", dataStr, e);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
