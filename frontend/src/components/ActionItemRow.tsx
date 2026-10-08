"use client";

import { useState } from "react";
import { Check, Clock, User, ArrowUpRight } from "lucide-react";
import { ActionItem } from "@/types/meeting";
import { updateActionItem } from "@/lib/api";
import { getPriorityColor } from "@/lib/utils";

interface ActionItemRowProps {
  item: ActionItem;
  onJumpToSegment?: (segmentId: number) => void;
  onStatusChanged?: (updated: ActionItem) => void;
}

export function ActionItemRow({
  item,
  onJumpToSegment,
  onStatusChanged,
}: ActionItemRowProps) {
  const [isCompleted, setIsCompleted] = useState(item.status === "completed");
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleStatus = async () => {
    const nextCompleted = !isCompleted;
    // Optimistic instant UI update
    setIsCompleted(nextCompleted);
    setIsUpdating(true);
    setError(null);

    try {
      const updated = await updateActionItem(item.id, {
        status: nextCompleted ? "completed" : "pending",
      });
      onStatusChanged?.(updated);
    } catch (err) {
      // Rollback on failure
      setIsCompleted(!nextCompleted);
      setError("Failed to sync");
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div
      className={`group flex items-start sm:items-center justify-between p-3.5 rounded-xl border transition-all ${
        isCompleted
          ? "bg-slate-900/40 border-slate-800/60 opacity-60"
          : "bg-surface-card/60 hover:bg-surface-card border-slate-800 hover:border-slate-700"
      }`}
    >
      <div className="flex items-start sm:items-center space-x-3 min-w-0 flex-1">
        {/* Optimistic Checkbox */}
        <button
          type="button"
          onClick={toggleStatus}
          disabled={isUpdating}
          className={`mt-0.5 sm:mt-0 flex-shrink-0 w-5 h-5 rounded-md border flex items-center justify-center transition-all ${
            isCompleted
              ? "bg-sky-500 border-sky-400 text-white"
              : "border-slate-600 hover:border-sky-400 bg-slate-900/80"
          }`}
          aria-label={isCompleted ? "Mark pending" : "Mark completed"}
        >
          {isCompleted && <Check className="w-3.5 h-3.5 stroke-[3]" />}
        </button>

        {/* Task description & metadata */}
        <div className="min-w-0 flex-1">
          <p
            className={`text-sm font-medium transition-colors ${
              isCompleted
                ? "line-through text-slate-400"
                : "text-slate-200 group-hover:text-white"
            }`}
          >
            {item.task}
          </p>

          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
            {item.owner_name && (
              <span className="flex items-center space-x-1">
                <User className="w-3 h-3 text-slate-400" />
                <span>{item.owner_name}</span>
              </span>
            )}

            {item.deadline && (
              <span className="flex items-center space-x-1">
                <Clock className="w-3 h-3 text-slate-400" />
                <span>{item.deadline}</span>
              </span>
            )}

            {error && (
              <span className="text-rose-400 text-[11px] font-medium">
                {error}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Badges & Jump anchor */}
      <div className="flex items-center space-x-2 flex-shrink-0 ml-3">
        <span
          className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full border ${getPriorityColor(
            item.priority
          )}`}
        >
          {item.priority}
        </span>

        {item.source_segment_ids && item.source_segment_ids.length > 0 && onJumpToSegment && (
          <button
            type="button"
            onClick={() => onJumpToSegment(item.source_segment_ids[0])}
            className="flex items-center space-x-1 text-[11px] font-medium text-sky-400 hover:text-sky-300 px-2 py-1 rounded-md bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/20 transition-colors"
            title={`Jump to segment ${item.source_segment_ids[0]}`}
          >
            <span>Seg #{item.source_segment_ids[0]}</span>
            <ArrowUpRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
