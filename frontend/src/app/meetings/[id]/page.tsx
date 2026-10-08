"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Clock,
  Users,
  Share2,
  HelpCircle,
  TrendingUp,
  CheckCircle2,
  FileText,
  AlertCircle,
  RefreshCw,
  ArrowLeft,
} from "lucide-react";
import { fetchMeeting, triggerMeetingProcessing } from "@/lib/api";
import { MeetingDetail } from "@/types/meeting";
import { formatDate, formatDuration, getStatusColor } from "@/lib/utils";
import { ActionItemRow } from "@/components/ActionItemRow";
import { DecisionCard } from "@/components/DecisionCard";
import { TranscriptViewer } from "@/components/TranscriptViewer";
import { ExportModal } from "@/components/ExportModal";

export default function MeetingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const meetingId = resolvedParams.id;

  const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState<number | null>(null);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchMeeting(meetingId);
      setMeeting(data);
    } catch (err) {
      console.error("Failed to load meeting:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll if in-progress
    const interval = setInterval(() => {
      if (
        meeting &&
        ["UPLOADED", "TRANSCRIBING", "EXTRACTING", "INDEXING"].includes(
          meeting.status
        )
      ) {
        loadData();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [meetingId, meeting?.status]);

  const handleRetryProcessing = async () => {
    setIsRetrying(true);
    try {
      const updated = await triggerMeetingProcessing(meetingId);
      setMeeting(updated);
    } catch (err) {
      console.error("Failed to re-process meeting:", err);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleJumpToSegment = (segId: number) => {
    setSelectedSegment(segId);
  };

  if (loading) {
    return (
      <div className="h-96 flex flex-col items-center justify-center space-y-4">
        <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading meeting intelligence...</p>
      </div>
    );
  }

  if (!meeting) {
    return (
      <div className="glass-card p-12 rounded-2xl text-center space-y-4">
        <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Meeting Not Found</h2>
        <p className="text-sm text-slate-400">
          The requested meeting ID could not be loaded.
        </p>
        <Link
          href="/meetings"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-slate-800 text-slate-200 text-xs font-semibold"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Directory</span>
        </Link>
      </div>
    );
  }

  const isProcessing = ["UPLOADED", "TRANSCRIBING", "EXTRACTING", "INDEXING"].includes(
    meeting.status
  );

  return (
    <div className="space-y-8">
      {/* Back button & Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          href="/meetings"
          className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Meetings</span>
        </Link>

        <div className="flex items-center space-x-3">
          {meeting.status === "FAILED" && (
            <button
              onClick={handleRetryProcessing}
              disabled={isRetrying}
              className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 flex items-center space-x-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRetrying ? "animate-spin" : ""}`} />
              <span>Retry Processing</span>
            </button>
          )}

          <button
            onClick={() => setIsExportOpen(true)}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center space-x-1.5 transition-colors shadow-sm"
          >
            <Share2 className="w-3.5 h-3.5 text-sky-400" />
            <span>Export Intelligence</span>
          </button>
        </div>
      </div>

      {/* Meeting Header Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span
            className={`text-[10px] uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full border ${getStatusColor(
              meeting.status
            )}`}
          >
            {meeting.status}
          </span>

          <span className="text-xs text-slate-400 flex items-center space-x-1">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{formatDate(meeting.meeting_date)}</span>
          </span>

          <span className="text-xs text-slate-400">•</span>

          <span className="text-xs text-slate-400 flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{formatDuration(meeting.duration_seconds)}</span>
          </span>

          <span className="text-xs text-slate-400">•</span>

          <span className="text-xs text-slate-400 capitalize">
            {meeting.source_type} source
          </span>
        </div>

        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            {meeting.title}
          </h1>
          {meeting.description && (
            <p className="mt-2 text-sm text-slate-400 max-w-3xl">
              {meeting.description}
            </p>
          )}
        </div>

        {/* Attendees */}
        {meeting.attendees && meeting.attendees.length > 0 && (
          <div className="pt-2 flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400 flex items-center space-x-1">
              <Users className="w-3.5 h-3.5" />
              <span>Participants:</span>
            </span>
            {meeting.attendees.map((att) => (
              <span
                key={att.id}
                className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60"
              >
                {att.display_name}
              </span>
            ))}
          </div>
        )}

        {/* Processing State Indicator */}
        {isProcessing && (
          <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center space-x-3 animate-pulse">
            <RefreshCw className="w-4 h-4 text-sky-400 animate-spin flex-shrink-0" />
            <div className="text-xs text-sky-300">
              <strong>Processing in Progress:</strong> {meeting.processing_stage}
            </div>
          </div>
        )}
      </div>

      {/* Two Column Layout: Structured Intel vs Transcript */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Summary, Decisions, Action Items, Questions */}
        <div className="lg:col-span-7 space-y-6">
          {/* Executive Summary */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-sky-400" />
              <h2 className="text-base font-bold text-white tracking-tight">
                Executive Summary
              </h2>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
              {meeting.summary || "No executive summary generated yet."}
            </p>
          </div>

          {/* Key Decisions */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  Key Decisions
                </h2>
              </div>
              <span className="text-xs text-slate-400">
                {meeting.decisions.length} recorded
              </span>
            </div>

            <div className="space-y-2.5">
              {meeting.decisions.length === 0 ? (
                <p className="text-xs text-slate-400 py-2">
                  No explicit decisions recorded for this session.
                </p>
              ) : (
                meeting.decisions.map((dec) => (
                  <DecisionCard
                    key={dec.id}
                    decision={dec}
                    onJumpToSegment={handleJumpToSegment}
                  />
                ))
              )}
            </div>
          </div>

          {/* Action Items with Optimistic UI */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-sky-400" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  Action Items
                </h2>
              </div>
              <span className="text-xs text-slate-400">
                {meeting.action_items.length} items
              </span>
            </div>

            <div className="space-y-2.5">
              {meeting.action_items.length === 0 ? (
                <p className="text-xs text-slate-400 py-2">
                  No action items assigned for this session.
                </p>
              ) : (
                meeting.action_items.map((action) => (
                  <ActionItemRow
                    key={action.id}
                    item={action}
                    onJumpToSegment={handleJumpToSegment}
                  />
                ))
              )}
            </div>
          </div>

          {/* Open Questions */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-purple-400" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  Open Questions & Dilemmas
                </h2>
              </div>
              <span className="text-xs text-slate-400">
                {meeting.open_questions.length} open
              </span>
            </div>

            <div className="space-y-2.5">
              {meeting.open_questions.length === 0 ? (
                <p className="text-xs text-slate-400 py-2">
                  No open dilemmas remaining.
                </p>
              ) : (
                meeting.open_questions.map((q) => (
                  <div
                    key={q.id}
                    className="p-3.5 rounded-xl bg-surface-card/60 border border-slate-800/80 flex items-start justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-slate-200">
                        {q.question}
                      </p>
                      {q.context && (
                        <p className="text-xs text-slate-400">{q.context}</p>
                      )}
                    </div>
                    {q.source_segment_ids && q.source_segment_ids.length > 0 && (
                      <button
                        type="button"
                        onClick={() => handleJumpToSegment(q.source_segment_ids[0])}
                        className="text-[11px] font-medium text-purple-400 hover:text-purple-300 px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/20 transition-colors flex-shrink-0"
                      >
                        Seg #{q.source_segment_ids[0]}
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Timestamped Transcript Viewer */}
        <div className="lg:col-span-5 sticky top-24">
          <TranscriptViewer
            segments={meeting.segments || []}
            selectedSegmentIndex={selectedSegment}
            onSelectSegment={(segIdx) => setSelectedSegment(segIdx)}
            audioUrl={meeting.audio_url}
          />
        </div>
      </div>

      {/* Export Modal */}
      <ExportModal
        meetingId={meeting.id}
        meetingTitle={meeting.title}
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
      />
    </div>
  );
}
