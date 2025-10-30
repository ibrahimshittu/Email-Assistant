const BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

export async function getAuthUrl() {
  const res = await fetch(`${BACKEND}/auth/nylas/url`);
  if (!res.ok) throw new Error("failed");
  return res.json();
}

export async function getMe() {
  const res = await fetch(`${BACKEND}/auth/me`, { cache: "no-store" });
  if (!res.ok) return { account: null };
  return res.json();
}

export async function syncLatest() {
  const res = await fetch(`${BACKEND}/sync/latest`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function chat(question: string, top_k = 6) {
  const res = await fetch(`${BACKEND}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
