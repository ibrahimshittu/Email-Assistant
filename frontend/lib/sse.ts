const BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

export function sseChat(
  question: string,
  onEvent: (evt: { event: string; data: any }) => void
) {
  const url = new URL(`${BACKEND}/chat/stream`);
  url.searchParams.set("question", question);
  const es = new EventSource(url.toString());
  es.addEventListener("message", (e) => {
    try {
      const payload = JSON.parse((e as MessageEvent).data);
      onEvent({ event: payload.event, data: payload.data });
    } catch {}
  });
  es.addEventListener("error", () => {
    es.close();
  });
  return es;
}
