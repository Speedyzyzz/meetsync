import Link from "next/link";
import { Calendar, Clock, PlusCircle, Mic, FileText, ArrowRight } from "lucide-react";
import { fetchMeetings } from "@/lib/api";
import { formatDate, formatDuration, getStatusColor } from "@/lib/utils";

import { Meeting } from "@/types/meeting";

export const revalidate = 0;

export default async function MeetingsPage() {
  let meetings: Meeting[] = [];
  try {
    meetings = await fetchMeetings();
  } catch (e) {
    console.error("Failed to load meetings:", e);
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Meeting Intelligence Directory
          </h1>
          <p className="text-sm text-slate-400">
            Browse, search, and inspect synthesized intelligence across all organizational meetings.
          </p>
        </div>

        <Link
          href="/upload"
          className="px-4 py-2 rounded-xl text-sm font-semibold bg-sky-500 hover:bg-sky-400 text-white shadow-md shadow-sky-500/20 transition-all flex items-center space-x-2 self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Meeting</span>
        </Link>
      </div>

      {/* Meetings List */}
      <div className="space-y-3">
        {meetings.length === 0 ? (
          <div className="glass-card p-12 rounded-2xl text-center space-y-3">
            <Calendar className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-base font-semibold text-slate-300">No meetings found</p>
            <p className="text-sm text-slate-500 max-w-sm mx-auto">
              Get started by uploading an audio recording or pasting a transcript from your meeting tool.
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-semibold hover:bg-sky-500/20 transition-colors"
            >
              <span>Ingest First Meeting</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          meetings.map((meeting) => (
            <Link
              key={meeting.id}
              href={`/meetings/${meeting.id}`}
              className="block glass-card p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition-all"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full border ${getStatusColor(
                        meeting.status
                      )}`}
                    >
                      {meeting.status}
                    </span>

                    <span className="flex items-center space-x-1 text-xs text-slate-400 px-2 py-0.5 rounded-full bg-slate-900 border border-slate-800">
                      {meeting.source_type === "audio" ? (
                        <Mic className="w-3 h-3 text-purple-400" />
                      ) : (
                        <FileText className="w-3 h-3 text-sky-400" />
                      )}
                      <span className="capitalize">{meeting.source_type}</span>
                    </span>

                    <span className="text-xs text-slate-400">
                      {formatDate(meeting.meeting_date)}
                    </span>
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs text-slate-400 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{formatDuration(meeting.duration_seconds)}</span>
                    </span>
                  </div>

                  <h2 className="text-lg font-bold text-white group-hover:text-sky-400 transition-colors truncate">
                    {meeting.title}
                  </h2>

                  {meeting.description && (
                    <p className="text-xs text-slate-400 line-clamp-1">
                      {meeting.description}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-6 flex-shrink-0 pt-3 md:pt-0 border-t md:border-t-0 border-slate-800">
                  <div className="text-right">
                    <p className="text-xs text-slate-400">Action Items</p>
                    <p className="text-sm font-bold text-sky-400">
                      {meeting.action_items_count}
                    </p>
                  </div>

                  <div className="text-right">
                    <p className="text-xs text-slate-400">Decisions</p>
                    <p className="text-sm font-bold text-emerald-400">
                      {meeting.decisions_count}
                    </p>
                  </div>

                  <div className="p-2 rounded-xl bg-slate-800/80 text-slate-400">
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
