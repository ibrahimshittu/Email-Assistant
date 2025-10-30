"use client";

import { useEffect, useState } from "react";
import { getAuthUrl, getMe } from "@/lib/api";

export default function ConnectPage() {
  const [account, setAccount] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getMe().then((res) => setAccount(res.account));
  }, []);

  const connect = async () => {
    setLoading(true);
    const { auth_url } = await getAuthUrl();
    window.location.href = auth_url;
  };

  return (
    <main className="space-y-4">
      <h2 className="text-lg font-semibold">Connect your email</h2>
      {account ? (
        <div className="rounded-md bg-green-50 p-3 text-green-800">
          Connected account ID: {account.id}
        </div>
      ) : (
        <button
          onClick={connect}
          disabled={loading}
          className="rounded-md bg-black px-3 py-2 text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {loading ? "Redirecting..." : "Connect with Nylas"}
        </button>
      )}
    </main>
  );
}
