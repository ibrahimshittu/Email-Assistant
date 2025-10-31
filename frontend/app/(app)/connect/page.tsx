"use client";

import { useEffect, useState } from "react";
import {
  getAuthUrl,
  getMe,
  syncLatest,
  type Account,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CheckCircle2, Mail, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function ConnectPage() {
  const router = useRouter();
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncCompleted, setSyncCompleted] = useState(false);

  useEffect(() => {
    getMe()
      .then((res) => setAccount(res.account))
      .finally(() => setLoading(false));
  }, []);

  const connect = async () => {
    setConnecting(true);
    try {
      const { auth_url } = await getAuthUrl();
      window.location.href = auth_url;
    } catch (error) {
      console.error("Failed to get auth URL:", error);
      setConnecting(false);
    }
  };

  const runSync = async () => {
    setSyncing(true);

    try {
      const res = await syncLatest();
      toast.success(`Successfully synced ${res.synced} messages!`);
      setSyncCompleted(true);
    } catch (e: any) {
      toast.error(e?.message || "Sync failed. Please try again.");
    } finally {
      setSyncing(false);
    }
  };

  const handleStartChatting = () => {
    router.push("/");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl w-full mx-auto space-y-6 flex flex-col items-center justify-center min-h-[80vh] px-4">
      <div className="text-center">
        <h2 className="text-3xl font-bold tracking-tight">
          Connect Your Email
        </h2>
        <p className="text-muted-foreground mt-2">
          Securely link your email account through Nylas to get started
        </p>
      </div>

      {account && (
        <Card className="border-gray-700 bg-gray-100 w-full">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-black text-white">
                    {account.email?.charAt(0).toUpperCase() || "U"}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle className="flex items-center gap-2 text-green-600">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    Connected
                  </CardTitle>
                  <CardDescription className="mt-1 text-gray-600">
                    Your account is successfully connected
                  </CardDescription>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="rounded-lg bg-white p-4 space-y-3 border border-gray-400">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-900 font-semibold">Email</span>
                <span className="font-medium text-gray-900">
                  {account.email}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-900 font-semibold">Account ID</span>
                <span className="font-mono text-xs text-gray-900">
                  {account.id}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-900 font-semibold">Provider</span>
                <span className="font-medium text-gray-900 capitalize">
                  {account.provider}
                </span>
              </div>
            </div>
            <div className="pt-4">
              <Button
                onClick={syncCompleted ? handleStartChatting : runSync}
                disabled={syncing}
                className="w-full bg-black hover:bg-gray-800 text-white"
                size="lg"
              >
                {syncing ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Syncing...
                  </>
                ) : syncCompleted ? (
                  "Start Chatting"
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Continue to Sync
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!account && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary/10 rounded-lg">
                <Mail className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle>No Account Connected</CardTitle>
                <CardDescription>
                  Connect your email to access AI-powered features
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>By connecting your email account, you'll be able to:</p>
              <ul className="space-y-2 ml-4">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>
                    Search and query your emails using natural language
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>Get AI-powered summaries and insights</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>Find information quickly across your entire inbox</span>
                </li>
              </ul>
            </div>
            <Button
              onClick={connect}
              disabled={connecting}
              className="w-full"
              size="lg"
            >
              {connecting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                "Connect with Nylas"
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
