import type { Metadata } from "next";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "MeetSync — AI-Powered Meeting Intelligence Platform",
  description: "Enterprise platform converting multi-speaker meetings into structured organizational knowledge.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 min-h-screen antialiased flex flex-col selection:bg-sky-500/20 selection:text-sky-300">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-400">
          MeetSync Intelligence Engine • FastAPI + Next.js 15 + PostgreSQL FTS
        </footer>
      </body>
    </html>
  );
}
