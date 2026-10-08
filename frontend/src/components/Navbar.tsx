"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, LayoutDashboard, Calendar, CheckSquare, Search, PlusCircle, Activity } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/meetings", label: "Meetings", icon: Calendar },
    { href: "/action-items", label: "Action Items", icon: CheckSquare },
    { href: "/search", label: "Search", icon: Search },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-border/70">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-8">
          <Link href="/dashboard" className="flex items-center space-x-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                MeetSync
              </span>
              <span className="ml-2 text-[10px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                AI Engine
              </span>
            </div>
          </Link>

          {/* Navigation links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || pathname.startsWith(`${link.href}/`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "text-sky-400 bg-sky-500/10 border border-sky-500/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Right action area */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-400 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800">
            <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span>FastAPI Core Online</span>
          </div>

          <Link
            href="/upload"
            className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md shadow-sky-500/20 hover:from-sky-400 hover:to-blue-500 transition-all hover:shadow-sky-500/30"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Meeting</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
