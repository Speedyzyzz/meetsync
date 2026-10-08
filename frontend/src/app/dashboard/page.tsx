import Link from "next/link";
import {
  Calendar,
  CheckCircle,
  Clock,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Coins,
  Cpu,
} from "lucide-react";
import { fetchMeetings, fetchMetrics, fetchActionItems } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { ActionItemRow } from "@/components/ActionItemRow";
import { formatDate, formatDuration, getStatusColor } from "@/lib/utils";

import { Meeting, UsageMetrics, ActionItem } from "@/types/meeting";

export const revalidate = 0;

export default async function DashboardPage() {
  let meetings: Meeting[] = [];
  let metrics: UsageMetrics | null = null;
  let actionItems: ActionItem[] = [];

  try {
    const [mList, met, act] = await Promise.all([
      fetchMeetings(),
      fetchMetrics(),
      fetchActionItems("pending"),
    ]);
    meetings = mList;
    metrics = met;
    actionItems = act;
  } catch (err) {
    console.error("Dashboard data load error:", err);
  }

  const recentMeetings = meetings.slice(0, 5);
  const pendingActions = actionItems.slice(0, 6);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Enterprise Intelligence Operational</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Meeting Intelligence Dashboard
            </h1>
            <p className="text-sm text-slate-400 max-w-xl">
              Turn unstructured team conversations into verified decisions, trackable action items, and timestamped organizational knowledge.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              href="/upload"
              className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-sky-500 hover:bg-sky-400 text-white shadow-lg shadow-sky-500/20 transition-all flex items-center space-x-2"
            >
              <span>+ Ingest Meeting</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Meetings"
          value={metrics?.meetings?.total ?? meetings.length}
          subtext={`${metrics?.meetings?.completed ?? 0} processed successfully`}
          icon={Calendar}
          badge="Sync Active"
          badgeColor="text-sky-400 bg-sky-500/10 border-sky-500/20"
        />

        <StatCard
          title="Pending Actions"
          value={metrics?.action_items?.pending ?? 0}
          subtext={`${metrics?.action_items?.completed ?? 0} items completed`}
          icon={CheckCircle}
          badge="High Priority"
          badgeColor="text-amber-400 bg-amber-500/10 border-amber-500/20"
        />

        <StatCard
          title="Key Decisions"
          value={metrics?.decisions?.total ?? 0}
          subtext="Extracted from conversations"
          icon={TrendingUp}
          badge="Agreed"
          badgeColor="text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
        />

        <StatCard
          title="AI Cost & Usage"
          value={`$${metrics?.ai_usage?.total_cost_usd?.toFixed(4) ?? "0.0000"}`}
          subtext={`${(metrics?.ai_usage?.total_tokens ?? 0).toLocaleString()} tokens consumed`}
          icon={Coins}
          badge="Cost Optimized"
          badgeColor="text-indigo-400 bg-indigo-500/10 border-indigo-500/20"
        />
      </div>

      {/* Content Split: Recent Meetings & Active Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Recent Meetings List */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-sky-400" />
              <span>Recent Meetings</span>
            </h2>
            <Link
              href="/meetings"
              className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center space-x-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3">
            {recentMeetings.length === 0 ? (
              <div className="glass-card p-8 rounded-2xl text-center text-sm text-slate-400">
                No meetings ingested yet. Upload an audio recording or paste a transcript to begin.
              </div>
            ) : (
              recentMeetings.map((meet) => (
                <Link
                  key={meet.id}
                  href={`/meetings/${meet.id}`}
                  className="block glass-card p-4 rounded-2xl border border-slate-800 hover:border-slate-700 transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${getStatusColor(
                            meet.status
                          )}`}
                        >
                          {meet.status}
                        </span>
                        <span className="text-xs text-slate-400">
                          {formatDate(meet.meeting_date)}
                        </span>
                        <span className="text-xs text-slate-400">•</span>
                        <span className="text-xs text-slate-400 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatDuration(meet.duration_seconds)}</span>
                        </span>
                      </div>

                      <h3 className="mt-1.5 text-base font-semibold text-white truncate">
                        {meet.title}
                      </h3>

                      {meet.summary && (
                        <p className="mt-1 text-xs text-slate-400 line-clamp-2">
                          {meet.summary}
                        </p>
                      )}

                      <div className="mt-3 flex items-center space-x-4 text-xs font-medium text-slate-400">
                        <span className="text-slate-300">
                          <strong className="text-sky-400">
                            {meet.action_items_count}
                          </strong>{" "}
                          action items
                        </span>
                        <span className="text-slate-300">
                          <strong className="text-emerald-400">
                            {meet.decisions_count}
                          </strong>{" "}
                          decisions
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Right: Urgent Action Items */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-amber-400" />
              <span>Pending Action Items</span>
            </h2>
            <Link
              href="/action-items"
              className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center space-x-1"
            >
              <span>Manage Board</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-2.5">
            {pendingActions.length === 0 ? (
              <div className="glass-card p-8 rounded-2xl text-center text-sm text-slate-400">
                All action items completed! No pending tasks remaining.
              </div>
            ) : (
              pendingActions.map((item) => (
                <ActionItemRow key={item.id} item={item} />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
