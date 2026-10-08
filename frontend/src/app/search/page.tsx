"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search as SearchIcon,
  Clock,
  ArrowRight,
  TrendingUp,
  FileText,
  Volume2,
  RefreshCw,
} from "lucide-react";
import { searchMeetings } from "@/lib/api";
import { SearchResultItem } from "@/types/meeting";
import { formatTimestamp } from "@/lib/utils";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSearched(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchMeetings(query.trim());
        setResults(res.results || []);
        setSearched(true);
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const getResultIcon = (type: string) => {
    switch (type) {
      case "transcript":
        return <Volume2 className="w-4 h-4 text-sky-400" />;
      case "decision":
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case "summary":
      default:
        return <FileText className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Search Header */}
      <div className="space-y-2 text-center">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Full-Text Organizational Knowledge Search
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Query across spoken transcripts, key decisions, executive summaries, and action item context in real-time.
        </p>
      </div>

      {/* Search Box */}
      <div className="relative">
        <SearchIcon className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search topics, decisions, or spoken phrases (e.g. 'launch Friday', 'QA', 'Redis', 'Jira')..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-slate-950 border border-slate-800 text-base text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 shadow-xl"
          autoFocus
        />
        {loading && (
          <RefreshCw className="w-5 h-5 text-sky-400 animate-spin absolute right-4 top-1/2 -translate-y-1/2" />
        )}
      </div>

      {/* Results List */}
      <div className="space-y-3">
        {searched && (
          <p className="text-xs text-slate-400 px-1">
            Found {results.length} result(s) for &ldquo;{query}&rdquo;
          </p>
        )}

        {results.map((res, index) => (
          <Link
            key={index}
            href={`/meetings/${res.meeting_id}`}
            className="block glass-card p-4 rounded-2xl border border-slate-800 hover:border-slate-700 transition-all"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <div className="p-1 rounded-md bg-slate-800/80">
                    {getResultIcon(res.result_type)}
                  </div>
                  <span className="text-xs font-semibold text-white truncate">
                    {res.meeting_title}
                  </span>
                  <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                    {res.result_type}
                  </span>
                  {res.speaker && (
                    <span className="text-xs text-slate-400 font-medium">
                      by {res.speaker}
                    </span>
                  )}
                </div>

                <p className="text-sm text-slate-300 line-clamp-2">
                  {res.snippet}
                </p>

                {res.timestamp_seconds != null && (
                  <div className="flex items-center space-x-1 text-xs text-sky-400 font-mono pt-1">
                    <Clock className="w-3 h-3" />
                    <span>Timestamp: {formatTimestamp(res.timestamp_seconds)}</span>
                  </div>
                )}
              </div>

              <div className="p-2 rounded-xl bg-slate-800/60 text-slate-400 flex-shrink-0">
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          </Link>
        ))}

        {searched && results.length === 0 && (
          <div className="glass-card p-12 rounded-2xl text-center text-sm text-slate-400">
            No matching intelligence found for &ldquo;{query}&rdquo;. Try another term.
          </div>
        )}
      </div>
    </div>
  );
}
