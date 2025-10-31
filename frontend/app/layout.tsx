import "../styles/globals.css";
import React from "react";

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
      <body className="min-h-screen bg-background antialiased dark">
        {children}
      </body>
    </html>
  );
}
