import "../styles/globals.css";
import React from "react";
import { Mail, MessageSquare, RefreshCw, Link as LinkIcon, BarChart3 } from "lucide-react";

export const metadata = {
  title: "Email Assistant",
  description: "Your AI-powered email assistant",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background antialiased">
        <div className="relative flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-16 items-center justify-between max-w-6xl">
              <div className="flex items-center gap-2">
                <Mail className="h-6 w-6 text-primary" />
                <h1 className="text-xl font-semibold">Email Assistant</h1>
              </div>
              <nav className="flex items-center gap-6">
                <a
                  className="flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary"
                  href="/connect"
                >
                  <LinkIcon className="h-4 w-4" />
                  <span className="hidden sm:inline">Connect</span>
                </a>
                <a
                  className="flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary"
                  href="/sync"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span className="hidden sm:inline">Sync</span>
                </a>
                <a
                  className="flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary"
                  href="/chat"
                >
                  <MessageSquare className="h-4 w-4" />
                  <span className="hidden sm:inline">Chat</span>
                </a>
                <a
                  className="flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary"
                  href="/eval"
                >
                  <BarChart3 className="h-4 w-4" />
                  <span className="hidden sm:inline">Eval</span>
                </a>
              </nav>
            </div>
          </header>
          <main className="flex-1">
            <div className="container max-w-6xl py-8">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
