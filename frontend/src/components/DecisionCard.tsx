import { CheckCircle2, ArrowUpRight } from "lucide-react";
import { Decision } from "@/types/meeting";

interface DecisionCardProps {
  decision: Decision;
  onJumpToSegment?: (segmentId: number) => void;
}

export function DecisionCard({ decision, onJumpToSegment }: DecisionCardProps) {
  return (
    <div className="p-3.5 rounded-xl bg-surface-card/60 border border-slate-800/80 hover:border-slate-700 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-2.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-slate-200">
              {decision.decision}
            </p>
            {decision.context && (
              <p className="mt-1 text-xs text-slate-400">
                {decision.context}
              </p>
            )}
          </div>
        </div>

        {decision.source_segment_ids && decision.source_segment_ids.length > 0 && onJumpToSegment && (
          <button
            type="button"
            onClick={() => onJumpToSegment(decision.source_segment_ids[0])}
            className="flex items-center space-x-1 text-[11px] font-medium text-emerald-400 hover:text-emerald-300 px-2 py-0.5 rounded-md bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 transition-colors flex-shrink-0 ml-3"
            title={`View evidence at segment ${decision.source_segment_ids[0]}`}
          >
            <span>Seg #{decision.source_segment_ids[0]}</span>
            <ArrowUpRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
