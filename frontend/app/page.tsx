"use client";

import { useState, useRef, useEffect } from "react";
import { flushSync } from "react-dom";
import { streamChat } from "@/lib/sse";
import {
  getMe,
  getAuthUrl,
  syncLatest,
  type Account,
  type ChatSource,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Send,
  Mail,
  Loader2,
  Sparkles,
  Link as LinkIcon,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}

export default function Page() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [account, setAccount] = useState<Account | null>(null);
  const [connectOpen, setConnectOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMe().then((res) => setAccount(res.account));
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleConnect = async () => {
    try {
      const { auth_url } = await getAuthUrl();
      window.location.href = auth_url;
    } catch (error) {
      console.error("Failed to connect:", error);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setSyncSuccess(false);
    try {
      await syncLatest();
      setSyncSuccess(true);
      setTimeout(() => setSyncSuccess(false), 3000);
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}-${Math.random()}`,
      role: "user",
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const assistantMessage: Message = {
      id: `assistant-${Date.now()}-${Math.random()}`,
      role: "assistant",
      content: "",
      sources: [],
    };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      await streamChat(input, { top_k: 6 }, (event) => {
        if (event.event === "sources") {
          console.log("📧 Received sources:", event.data.sources);
          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
              updated[lastIndex] = {
                ...updated[lastIndex],
                sources: event.data.sources || [],
              };
              console.log(
                "✅ Updated message with sources:",
                updated[lastIndex]
              );
              return [...updated]; // Create new array reference
            }
            return updated;
          });
        } else if (event.event === "token") {
          const token = event.data.token || "";
          if (!token) return;

          // Use flushSync to force immediate rendering of each token
          flushSync(() => {
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: updated[lastIndex].content + token,
                };
                return [...updated];
              }
              return updated;
            });
          });
        } else if (event.event === "done") {
          setLoading(false);
        }
      });
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === "assistant") {
          last.content =
            "Sorry, I encountered an error. Please connect and sync your emails first.";
        }
        return updated;
      });
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!account) {
    return (
      <div className="h-screen w-full flex flex-col items-center justify-center text-center p-4">
        <div className="max-w-md w-full">
          <h1 className="text-3xl font-bold mb-1">Connect Your Email</h1>
          <p className="text-muted-foreground mb-6">
            Securely link your email account through Nylas to get started
          </p>
          <Button onClick={handleConnect} className="w-full">
            <LinkIcon className="mr-2 h-4 w-4" />
            Connect with Nylas
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex items-start justify-center p-3 md:p-6">
      <div className="w-full max-w-lg sm:max-w-xl md:max-w-2xl lg:max-w-3xl xl:max-w-4xl h-[calc(100vh-24px)] md:h-[calc(100vh-48px)] rounded-2xl border bg-background shadow-sm flex flex-col">
        {/* Header */}
        <div className="h-12 md:h-14 border-b px-3 md:px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            <span className="font-semibold">
              Email
              <span className="text-xs text-muted-foreground"> Assistant</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Button
              size="sm"
              variant="ghost"
              onClick={handleSync}
              disabled={!account || syncing}
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : syncSuccess ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  <span>Sync Emails</span>
                </>
              )}
            </Button>
            <Dialog open={connectOpen} onOpenChange={setConnectOpen}>
              <DialogTrigger asChild>
                <Button size="sm" variant={account ? "ghost" : "default"}>
                  <LinkIcon className="h-4 w-4 mr-2" />
                  {account ? "Account" : "Connect"}
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>
                    {account ? "Connected Account" : "Connect Your Email"}
                  </DialogTitle>
                  <DialogDescription>
                    {account
                      ? "Your email account is connected and ready to use."
                      : "Link your email account to start chatting with your inbox."}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  {account ? (
                    <div className="rounded-lg border p-4 space-y-2">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback className="bg-primary text-primary-foreground">
                            {account.email?.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{account.email}</p>
                          <p className="text-xs text-muted-foreground">
                            Account ID: {account.id}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <Button onClick={handleConnect} className="w-full">
                      <LinkIcon className="mr-2 h-4 w-4" />
                      Connect with Nylas
                    </Button>
                  )}
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Body */}
        <ScrollArea className="flex-1 px-4 md:px-6 py-6" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center min-h-[calc(100vh-300px)] text-center px-4">
              <h1 className="text-2xl text-primary md:text-3xl font-semibold mb-2">
                What can I help with?
              </h1>
              <p className="text-muted-foreground mb-2 max-w-md">
                Ask me anything about your emails. I can help you find messages,
                summarize threads, and extract information.
              </p>
            </div>
          ) : (
            <div className="space-y-6 pb-2">
              {messages.map((message) => (
                <div key={message.id} className="flex flex-col gap-4">
                  {message.role === "user" ? (
                    <div className="flex justify-end">
                      <div className="bg-primary/20 rounded-2xl px-4 py-2.5 inline-block max-w-[80%] text-sm">
                        {message.content}
                      </div>
                    </div>
                  ) : (
                    <div className="flex gap-3 items-start">
                      <Avatar className="h-8 w-8 shrink-0 mt-1">
                        <AvatarFallback className="bg-muted text-muted-foreground border border-border">
                          AI
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 space-y-2 min-w-0">
                        <div className="bg-muted/50 rounded-2xl px-4 py-3 inline-block max-w-[85%]">
                          {message.content ? (
                            <p className="text-sm whitespace-pre-wrap leading-relaxed">
                              {message.content}
                            </p>
                          ) : (
                            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                          )}
                        </div>
                        {message.sources && message.sources.length > 0 && (
                          <Dialog>
                            <DialogTrigger asChild>
                              <button className="text-xs font-medium text-muted-foreground hover:text-foreground flex items-center gap-1.5 px-3 py-1.5 rounded-md hover:bg-accent transition-colors">
                                <Mail className="h-3 w-3" />
                                {message.sources.length}{" "}
                                {message.sources.length === 1
                                  ? "Source"
                                  : "Sources"}
                              </button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                              <DialogHeader>
                                <DialogTitle>
                                  Email Sources ({message.sources.length})
                                </DialogTitle>
                                <DialogDescription>
                                  These emails were used to generate the
                                  response
                                </DialogDescription>
                              </DialogHeader>
                              <div className="space-y-3 mt-4">
                                {message.sources.map((source, idx) => (
                                  <div
                                    key={idx}
                                    className="rounded-lg border bg-card p-4 space-y-2 hover:bg-accent/50 transition-colors"
                                  >
                                    <div className="font-medium text-sm">
                                      {source.subject}
                                    </div>
                                    <div className="text-muted-foreground text-xs">
                                      <div className="flex items-center gap-2">
                                        <span>From: {source.from_addr}</span>
                                        <span>•</span>
                                        <span>
                                          {new Date(
                                            source.date
                                          ).toLocaleDateString("en-US", {
                                            month: "short",
                                            day: "numeric",
                                            year: "numeric",
                                          })}
                                        </span>
                                      </div>
                                    </div>
                                    {source.text && (
                                      <p className="text-muted-foreground text-xs leading-relaxed pt-2 border-t">
                                        {source.text}
                                      </p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </DialogContent>
                          </Dialog>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Input */}
        <div className="px-4 md:px-6 py-4 border-t">
          <div className="relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter a prompt here"
              disabled={loading}
              className="pr-12 h-12 text-base"
            />
            <Button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              size="icon"
              className="absolute right-1 top-1 h-10 w-10"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-[11px] text-muted-foreground mt-2 text-center">
            AI can make mistakes, so double-check responses.
          </p>
        </div>
      </div>
    </div>
  );
}
