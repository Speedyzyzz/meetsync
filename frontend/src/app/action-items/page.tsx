"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckSquare, ArrowUpRight, Filter, RefreshCw, CheckCircle2 } from "lucide-react";
import { fetchActionItems } from "@/lib/api";
import { ActionItem } from "@/types/meeting";
import { ActionItemRow } from "@/components/ActionItemRow";

export default function ActionItemsPage() {
  const [items, setItems] = useState<ActionItem[]>([]);
  const [filter, setFilter] = useState<"all" | "pending" | "completed">("all");
  const [loading, setLoading] = useState(true);

  const loadItems = async () => {
    try {
      setLoading(true);
      const data = await fetchActionItems(filter === "all" ? undefined : filter);
      setItems(data);
    } catch (err) {
      console.error("Failed to load action items:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, [filter]);

  const handleStatusChanged = (updated: ActionItem) => {
    setItems((prev) =>
      prev.map((i) => (i.id === updated.id ? updated : i))
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <CheckSquare className="w-6 h-6 text-sky-400" />
            <span>Workspace Action Items</span>
          </h1>
          <p className="text-sm text-slate-400">
            Track and complete assigned tasks across all synchronized meetings.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center space-x-2 p-1 rounded-xl bg-slate-900 border border-slate-800 self-start sm:self-auto">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              filter === "all"
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            All Items
          </button>

          <button
            onClick={() => setFilter("pending")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              filter === "pending"
                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Pending
          </button>

          <button
            onClick={() => setFilter("completed")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              filter === "completed"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Completed
          </button>
        </div>
      </div>

      {/* List */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-3">
        {loading ? (
          <div className="h-48 flex items-center justify-center space-x-2 text-slate-400 text-sm">
            <RefreshCw className="w-5 h-5 text-sky-400 animate-spin" />
            <span>Loading action items...</span>
          </div>
        ) : items.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center space-y-2 text-slate-500 text-sm">
            <CheckCircle2 className="w-8 h-8 text-slate-600" />
            <p>No action items found for current filter.</p>
          </div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="relative group">
              <ActionItemRow
                item={item}
                onStatusChanged={handleStatusChanged}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
