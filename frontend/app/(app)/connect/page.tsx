"use client";

import { useEffect, useState } from "react";
import { getAuthUrl, getMe, type Account } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CheckCircle2, Mail, Loader2 } from "lucide-react";

export default function ConnectPage() {
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Connect Your Email</h2>
        <p className="text-muted-foreground mt-2">
          Securely link your email account through Nylas to get started
        </p>
      </div>

      {account ? (
        <Card className="border-green-200 bg-green-50/50">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    {account.email?.charAt(0).toUpperCase() || "U"}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    Connected
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Your account is successfully connected
                  </CardDescription>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="rounded-lg bg-white p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Email</span>
                <span className="font-medium">{account.email}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Account ID</span>
                <span className="font-mono text-xs">{account.id}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Provider</span>
                <span className="font-medium capitalize">{account.provider}</span>
              </div>
            </div>
            <div className="pt-4 flex gap-3">
              <Button asChild variant="outline" className="flex-1">
                <a href="/sync">
                  Continue to Sync
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
      ) : (
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
              <p>
                By connecting your email account, you'll be able to:
              </p>
              <ul className="space-y-2 ml-4">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <span>Search and query your emails using natural language</span>
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
