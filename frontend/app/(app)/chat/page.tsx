"use client";

import { useState, useRef, useEffect } from "react";
import { streamChat } from "@/lib/sse";
import type { ChatSource } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, Bot, User, Mail, Calendar, Loader2, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const assistantMessage: Message = { role: "assistant", content: "", sources: [] };
    setMessages((prev) => [...prev, assistantMessage]);

    try {
      await streamChat(
        input,
        { top_k: 6 },
        (event) => {
          if (event.event === "sources") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === "assistant") {
                last.sources = event.data.sources || [];
              }
              return updated;
            });
          } else if (event.event === "token") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last.role === "assistant") {
                last.content += event.data.token || "";
              }
              return updated;
            });
          } else if (event.event === "done") {
            setLoading(false);
          } else if (event.event === "error") {
            console.error("Stream error:", event.data.error);
            setLoading(false);
          }
        }
      );
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.role === "assistant") {
          last.content = "Sorry, I encountered an error. Please try again or make sure you've connected and synced your emails.";
        }
        return updated;
      });
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-4xl mx-auto">
      <div className="mb-4">
        <h2 className="text-3xl font-bold tracking-tight">Chat with Your Emails</h2>
        <p className="text-muted-foreground mt-2">
          Ask questions in natural language and get AI-powered answers
        </p>
      </div>

      <Card className="flex-1 flex flex-col">
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-8">
              <div className="p-4 bg-primary/10 rounded-full mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Ask me anything about your emails. For example:
              </p>
              <div className="mt-4 space-y-2 text-left">
                <div className="text-sm text-muted-foreground bg-muted/50 rounded-lg p-3">
                  "What emails did I receive from John last week?"
                </div>
                <div className="text-sm text-muted-foreground bg-muted/50 rounded-lg p-3">
                  "Summarize my recent project updates"
                </div>
                <div className="text-sm text-muted-foreground bg-muted/50 rounded-lg p-3">
                  "Find emails about the Q4 budget"
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.role === "assistant" && (
                    <Avatar className="h-8 w-8 border">
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                  <div className={`flex flex-col gap-2 max-w-[80%]`}>
                    <div
                      className={`rounded-lg px-4 py-3 ${
                        message.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      {loading && message.role === "assistant" && !message.content && (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      )}
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground font-medium">
                          Sources ({message.sources.length})
                        </p>
                        <div className="space-y-2">
                          {message.sources.map((source, idx) => (
                            <div
                              key={idx}
                              className="rounded-lg border bg-card p-3 text-xs space-y-1"
                            >
                              <div className="font-medium flex items-center gap-2">
                                <Mail className="h-3 w-3 text-primary" />
                                {source.subject}
                              </div>
                              <div className="text-muted-foreground flex items-center gap-2">
                                <Calendar className="h-3 w-3" />
                                {new Date(source.date).toLocaleDateString()}
                                {" • "}
                                From: {source.from_addr}
                              </div>
                              {source.snippet && (
                                <p className="text-muted-foreground line-clamp-2 mt-1">
                                  {source.snippet}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {message.role === "user" && (
                    <Avatar className="h-8 w-8 border">
                      <AvatarFallback className="bg-secondary">
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <CardContent className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your emails..."
              disabled={loading}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              size="icon"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
