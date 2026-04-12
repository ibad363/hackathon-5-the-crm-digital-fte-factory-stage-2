import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FTE Factory — AI Customer Support",
  description: "24/7 AI-Powered Customer Support Portal — Resolve tickets in minutes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 dark:bg-slate-950">
        <Navbar />
        <main className="flex-1 flex flex-col">
          {children}
        </main>
        <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-sm text-slate-500 dark:text-slate-500">
          <p>© 2026 FTE Factory · Built with OpenAI Agents SDK + FastAPI</p>
        </footer>
      </body>
    </html>
  );
}
