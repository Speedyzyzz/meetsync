export interface TranscriptSegment {
  id: string;
  transcript_id: string;
  meeting_id: string;
  segment_index: number;
  speaker: string;
  start_time: number;
  end_time: number;
  text: string;
}

export interface Decision {
  id: string;
  meeting_id: string;
  decision: string;
  context?: string | null;
  source_segment_ids: number[];
  created_at: string;
}

export interface ActionItem {
  id: string;
  meeting_id: string;
  task: string;
  owner_id?: string | null;
  owner_name?: string | null;
  deadline?: string | null;
  priority: "low" | "medium" | "high";
  status: "pending" | "in_progress" | "completed" | "cancelled";
  source_segment_ids: number[];
  created_at: string;
  completed_at?: string | null;
}

export interface OpenQuestion {
  id: string;
  meeting_id: string;
  question: string;
  context?: string | null;
  resolved: boolean;
  resolved_at?: string | null;
  resolved_by?: string | null;
  source_segment_ids: number[];
  created_at: string;
}

export interface Attendee {
  id: string;
  meeting_id: string;
  display_name: string;
  email?: string | null;
}

export interface Meeting {
  id: string;
  workspace_id: string;
  title: string;
  description?: string | null;
  meeting_date: string;
  duration_seconds: number;
  source_type: "audio" | "transcript";
  status: "UPLOADED" | "TRANSCRIBING" | "TRANSCRIBED" | "EXTRACTING" | "EXTRACTED" | "INDEXING" | "COMPLETED" | "FAILED";
  processing_stage: string;
  error_message?: string | null;
  audio_url?: string | null;
  retry_count: number;
  token_count: number;
  cost_usd: number;
  summary?: string | null;
  action_items_count: number;
  decisions_count: number;
  created_at: string;
  updated_at: string;
}

export interface MeetingDetail extends Meeting {
  attendees: Attendee[];
  segments: TranscriptSegment[];
  decisions: Decision[];
  action_items: ActionItem[];
  open_questions: OpenQuestion[];
}

export interface ProcessingJob {
  id: string;
  meeting_id: string;
  status: string;
  current_step: string;
  progress_percent: number;
  error_message?: string | null;
  retry_count: number;
  started_at: string;
  completed_at?: string | null;
}

export interface SearchResultItem {
  meeting_id: string;
  meeting_title: string;
  result_type: "transcript" | "decision" | "action_item" | "summary";
  snippet: string;
  matched_segment_id?: number | null;
  timestamp_seconds?: number | null;
  speaker?: string | null;
}

export interface UsageMetrics {
  meetings: {
    total: number;
    completed: number;
  };
  action_items: {
    total: number;
    completed: number;
    pending: number;
  };
  decisions: {
    total: number;
  };
  ai_usage: {
    total_tokens: number;
    total_cost_usd: number;
    average_cost_per_meeting_usd: number;
  };
}
