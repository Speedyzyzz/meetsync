"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Play, Volume2, Clock, User } from "lucide-react";
import { TranscriptSegment } from "@/types/meeting";
import { formatTimestamp } from "@/lib/utils";

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  selectedSegmentIndex?: number | null;
  onSelectSegment?: (segmentIndex: number) => void;
  audioUrl?: string | null;
}

const SPEAKER_COLORS = [
  "text-sky-400 bg-sky-500/10 border-sky-500/20",
  "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
  "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  "text-amber-400 bg-amber-500/10 border-amber-500/20",
  "text-purple-400 bg-purple-500/10 border-purple-500/20",
  "text-rose-400 bg-rose-500/10 border-rose-500/20",
];

function getSpeakerColor(speaker: string) {
  let hash = 0;
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
  }
  const idx = Math.abs(hash) % SPEAKER_COLORS.length;
  return SPEAKER_COLORS[idx];
}

export function TranscriptViewer({
  segments,
  selectedSegmentIndex,
  onSelectSegment,
  audioUrl,
}: TranscriptViewerProps) {
  const [filterQuery, setFilterQuery] = useState("");
  const [activeSeg, setActiveSeg] = useState<number | null>(selectedSegmentIndex || null);
  const segmentRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});

  useEffect(() => {
    if (selectedSegmentIndex != null) {
      setActiveSeg(selectedSegmentIndex);
      const el = segmentRefs.current[selectedSegmentIndex];
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [selectedSegmentIndex]);

  const filteredSegments = segments.filter((seg) => {
    if (!filterQuery.trim()) return true;
    const q = filterQuery.toLowerCase();
    return (
      seg.text.toLowerCase().includes(q) ||
      seg.speaker.toLowerCase().includes(q)
    );
  });

  return (
    <div className="glass-card rounded-2xl flex flex-col h-[650px] overflow-hidden border border-slate-800">
      {/* Viewer Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Volume2 className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Interactive Transcript
          </h3>
          <span className="text-xs text-slate-400">
            ({segments.length} segments)
          </span>
        </div>

        {/* Search bar within transcript */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search transcript text..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-sky-500"
          />
        </div>
      </div>

      {/* Audio player if audio source is available */}
      {audioUrl && (
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/60 flex items-center justify-between">
          <span className="text-xs text-slate-400 flex items-center space-x-1.5">
            <Play className="w-3 h-3 text-sky-400 fill-sky-400" />
            <span>Audio stream synchronized</span>
          </span>
          <audio controls className="h-7 max-w-xs" src={audioUrl}>
            Your browser does not support audio playback.
          </audio>
        </div>
      )}

      {/* Scrollable Transcript Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
        {filteredSegments.length === 0 ? (
          <div className="h-40 flex items-center justify-center text-sm text-slate-400">
            No transcript segments matched your filter query.
          </div>
        ) : (
          filteredSegments.map((seg) => {
            const isSelected = activeSeg === seg.segment_index;
            const speakerColor = getSpeakerColor(seg.speaker);

            return (
              <div
                key={seg.id || seg.segment_index}
                ref={(el) => {
                  segmentRefs.current[seg.segment_index] = el;
                }}
                onClick={() => {
                  setActiveSeg(seg.segment_index);
                  onSelectSegment?.(seg.segment_index);
                }}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? "bg-sky-500/10 border-sky-500/40 ring-1 ring-sky-500/30"
                    : "bg-surface-card/40 hover:bg-surface-card/80 border-slate-800/60 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${speakerColor}`}
                    >
                      {seg.speaker}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Seg #{seg.segment_index}
                    </span>
                  </div>

                  <div className="flex items-center space-x-1 text-[11px] font-mono text-slate-400">
                    <Clock className="w-3 h-3" />
                    <span>{formatTimestamp(seg.start_time)}</span>
                  </div>
                </div>

                <p className="text-sm text-slate-300 leading-relaxed">
                  {seg.text}
                </p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
