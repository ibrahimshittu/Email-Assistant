"use client";

import { useState } from "react";
import { syncLatest, type SyncResponse } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RefreshCw, CheckCircle2, AlertCircle, Database, Inbox } from "lucide-react";

export default function SyncPage() {
  const [syncResult, setSyncResult] = useState<SyncResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const runSync = async () => {
    setLoading(true);
    setError("");
    setSyncResult(null);

    try {
      const res = await syncLatest();
      setSyncResult(res);
    } catch (e: any) {
      setError(e?.message || "Sync failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Sync & Index Emails</h2>
        <p className="text-muted-foreground mt-2">
          Fetch and index your latest emails to enable AI-powered search
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary/10 rounded-lg">
              <RefreshCw className="h-6 w-6 text-primary" />
            </div>
            <div>
              <CardTitle>Email Synchronization</CardTitle>
              <CardDescription>
                Sync your latest 200 messages and index them for search
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              This process will:
            </p>
            <ul className="space-y-2 ml-4">
              <li className="flex items-start gap-2">
                <Inbox className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <span>Fetch your latest 200 email messages</span>
              </li>
              <li className="flex items-start gap-2">
                <Database className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <span>Index messages into vector database for semantic search</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                <span>Make your emails searchable via AI chat interface</span>
              </li>
            </ul>
          </div>

          <Button
            onClick={runSync}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Sync Last 200 Messages
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {syncResult && (
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700">
              <CheckCircle2 className="h-5 w-5" />
              Sync Completed Successfully
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg bg-white p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Messages Synced</span>
                <span className="text-2xl font-bold text-green-700">
                  {syncResult.synced}
                </span>
              </div>
              <div className="h-px bg-border" />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Chunks Indexed</span>
                <span className="text-2xl font-bold text-green-700">
                  {syncResult.indexed_chunks}
                </span>
              </div>
            </div>
            <div className="mt-4 flex gap-3">
              <Button asChild variant="outline" className="flex-1">
                <a href="/sync">
                  Sync Again
                </a>
              </Button>
              <Button asChild className="flex-1">
                <a href="/chat">
                  Start Chatting
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-destructive/50 bg-destructive/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              Sync Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-destructive/90">{error}</p>
            <p className="text-xs text-muted-foreground mt-2">
              Make sure you have connected your email account first.
            </p>
            <Button asChild variant="outline" className="mt-4">
              <a href="/connect">
                Go to Connect
              </a>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
