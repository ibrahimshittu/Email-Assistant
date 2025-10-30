import "../styles/globals.css";
import React from "react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 text-gray-900">
        <div className="mx-auto max-w-5xl p-6">
          <header className="mb-6 flex items-center justify-between">
            <h1 className="text-xl font-semibold">Email Assistant</h1>
            <nav className="gap-4 hidden sm:flex">
              <a className="hover:underline" href="/connect">
                Connect
              </a>
              <a className="hover:underline" href="/sync">
                Sync
              </a>
              <a className="hover:underline" href="/chat">
                Chat
              </a>
              <a className="hover:underline" href="/eval">
                Eval
              </a>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
