import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, MessageSquare, RefreshCw, Sparkles } from "lucide-react";

export default function Page() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col items-center text-center gap-4 py-12">
        <div className="inline-flex items-center justify-center p-2 bg-primary/10 rounded-full mb-2">
          <Mail className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight">
          Welcome to Email Assistant
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl">
          Your AI-powered email companion. Connect your email, sync your messages, and chat with your inbox using natural language.
        </p>
        <div className="flex gap-4 mt-4">
          <Button asChild size="lg">
            <Link href="/connect">
              Get Started
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/chat">
              Try Chat
            </Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Mail className="h-5 w-5 text-primary" />
              </div>
              <CardTitle>Connect</CardTitle>
            </div>
            <CardDescription>
              Link your email account securely through Nylas
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Authenticate once and start accessing your emails through our intelligent interface.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary/10 rounded-lg">
                <RefreshCw className="h-5 w-5 text-primary" />
              </div>
              <CardTitle>Sync</CardTitle>
            </div>
            <CardDescription>
              Keep your emails up to date and indexed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Automatically sync and index your latest messages for fast, intelligent search.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary/10 rounded-lg">
                <MessageSquare className="h-5 w-5 text-primary" />
              </div>
              <CardTitle>Chat</CardTitle>
            </div>
            <CardDescription>
              Ask questions about your emails naturally
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Use AI to find information, summarize threads, and get insights from your inbox.
            </p>
          </CardContent>
        </Card>
      </section>

      <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-primary/10">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <CardTitle>Powered by AI</CardTitle>
          </div>
          <CardDescription>
            Advanced RAG (Retrieval-Augmented Generation) technology
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm">
            Our email assistant uses state-of-the-art language models and vector search to understand your questions and provide accurate, contextual answers from your email history.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
