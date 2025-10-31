const BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000";

export interface Account {
  id: number;
  email: string;
  provider: string;
  nylas_grant_id?: string;
  created_at?: string;
}

export interface AuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface MeResponse {
  account: Account | null;
}

export interface SyncResponse {
  synced: number;
  indexed_chunks: number;
}

export interface ChatSource {
  message_id: string;
  subject: string;
  from_addr: string;
  date: string;
  thread_id: string;
  text: string;
  chunk_index: number;
  snippet?: string;
  score?: number;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  metadata?: Record<string, any>;
}

export async function getAuthUrl(): Promise<AuthUrlResponse> {
  const res = await fetch(`${BACKEND}/auth/nylas/url`);
  if (!res.ok) throw new Error("Failed to get auth URL");
  return res.json();
}

export async function getMe(): Promise<MeResponse> {
  const res = await fetch(`${BACKEND}/auth/me`, { cache: "no-store" });
  if (!res.ok) return { account: null };
  return res.json();
}

export async function syncLatest(): Promise<SyncResponse> {
  const res = await fetch(`${BACKEND}/sync/latest`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
