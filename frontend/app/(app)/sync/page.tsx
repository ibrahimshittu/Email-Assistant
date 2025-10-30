"use client";

import { useState } from "react";
import { syncLatest } from "@/lib/api";

export default function SyncPage() {
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const runSync = async () => {
    setLoading(true);
    try {
      const res = await syncLatest();
      setStatus(
        `Synced ${res.synced} messages, indexed ${res.indexed_chunks} chunks`
      );
    } catch (e: any) {
      setStatus(e?.message || "Sync failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="space-y-4">
      <h2 className="text-lg font-semibold">Sync and Index</h2>
      <button
        onClick={runSync}
        disabled={loading}
        className="rounded-md bg-black px-3 py-2 text-white hover:bg-gray-800 disabled:opacity-50"
      >
        {loading ? "Syncing..." : "Fetch last 200"}
      </button>
      {status && <div className="rounded-md bg-gray-100 p-3">{status}</div>}
    </main>
  );
}
