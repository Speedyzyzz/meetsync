"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Mic,
  UploadCloud,
  Sparkles,
  ArrowRight,
  RefreshCw,
  CheckCircle,
  HelpCircle,
} from "lucide-react";
import { createMeeting, uploadAudioMeeting } from "@/lib/api";

const SAMPLE_TRANSCRIPT_DEMO = `00:00:00 Arun: Welcome everyone to our Product Launch Strategy sync. We need to decide whether we are ready for launch this week and resolve any outstanding blockers.
00:00:25 Sarah: Thanks Arun. Engineering has finished the core API migration and frontend components. I propose we move the launch to Friday so we have adequate buffer for sanity checks.
00:00:52 Ravi: I agree with moving to Friday. That gives me enough time to complete the comprehensive QA regression test suite by Thursday EOD.
00:01:15 Arun: Excellent. Decision finalized: launch is officially moved to Friday. Also, we will begin the rollout with a 10% canary traffic allocation before 100% rollout.
00:01:40 Elena: That makes sense. I will update the developer API documentation by October 12 so partners have current guides.
00:02:05 Sarah: I will prepare the public rollout announcement and customer email templates by Friday morning.
00:02:30 Arun: I will coordinate the deployment window and monitor cloud database read replicas.
00:02:55 Elena: One open question: Who owns direct customer communication if any edge cases occur during migration?
00:03:20 Ravi: Another question: Do we need additional cloud infrastructure or auto-scaling buffers for the expected traffic spike?`;

export default function UploadPage() {
  const router = useRouter();

  const [mode, setMode] = useState<"transcript" | "audio">("transcript");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [attendees, setAttendees] = useState("");
  const [transcriptText, setTranscriptText] = useState("");
  const [audioFile, setAudioFile] = useState<File | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStage, setSubmitStage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const loadSampleTranscript = () => {
    setTitle("Product Launch Strategy Sync");
    setDescription("Discussion on launch timelines, QA regression testing, and traffic canary deployment.");
    setAttendees("Arun, Sarah, Ravi, Elena");
    setTranscriptText(SAMPLE_TRANSCRIPT_DEMO);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please provide a meeting title");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      setSubmitStage("Uploading meeting payload...");
      const attendeeList = attendees
        .split(",")
        .map((a) => a.trim())
        .filter(Boolean);

      let createdMeeting;

      if (mode === "transcript") {
        if (!transcriptText.trim()) {
          throw new Error("Please paste or write a meeting transcript");
        }
        setSubmitStage("Executing structured LLM extraction...");
        createdMeeting = await createMeeting({
          title,
          description: description || undefined,
          transcript_text: transcriptText,
          attendee_names: attendeeList,
        });
      } else {
        if (!audioFile) {
          throw new Error("Please select an audio file to upload");
        }
        setSubmitStage("Uploading audio and transcribing via Whisper...");
        const formData = new FormData();
        formData.append("title", title);
        if (description) formData.append("description", description);
        formData.append("file", audioFile);
        createdMeeting = await uploadAudioMeeting(formData);
      }

      setSubmitStage("Intelligence synthesized! Redirecting...");
      setTimeout(() => {
        router.push(`/meetings/${createdMeeting.id}`);
      }, 500);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to process meeting");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Page Title */}
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Ingest Meeting Intelligence
        </h1>
        <p className="text-sm text-slate-400">
          Upload recorded audio or paste raw meeting transcripts to trigger automated speaker segmentation, executive summarization, and task extraction.
        </p>
      </div>

      {/* Tabs */}
      <div className="p-1 rounded-xl bg-slate-900 border border-slate-800 flex items-center max-w-md">
        <button
          type="button"
          onClick={() => setMode("transcript")}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-semibold transition-all ${
            mode === "transcript"
              ? "bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Paste Transcript</span>
        </button>

        <button
          type="button"
          onClick={() => setMode("audio")}
          className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-xs font-semibold transition-all ${
            mode === "audio"
              ? "bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Mic className="w-4 h-4" />
          <span>Upload Audio File</span>
        </button>
      </div>

      {/* Form Container */}
      <form onSubmit={handleSubmit} className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 space-y-6">
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-400">
            {error}
          </div>
        )}

        {/* Title */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Meeting Title <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Q4 Sprint Planning Sync"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isSubmitting}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>

        {/* Description */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Meeting Description (Optional)
          </label>
          <input
            type="text"
            placeholder="Key objectives, agenda, or background notes..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={isSubmitting}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>

        {/* Attendees */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-300">
            Attendees (Comma-separated)
          </label>
          <input
            type="text"
            placeholder="e.g. Sarah, Arun, Ravi, Elena"
            value={attendees}
            onChange={(e) => setAttendees(e.target.value)}
            disabled={isSubmitting}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>

        {/* Mode 1: Paste Transcript */}
        {mode === "transcript" && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300">
                Transcript Content <span className="text-rose-400">*</span>
              </label>

              <button
                type="button"
                onClick={loadSampleTranscript}
                className="inline-flex items-center space-x-1.5 text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Load Sample Transcript</span>
              </button>
            </div>

            <textarea
              required
              rows={10}
              placeholder="00:04:12 Sarah: Let's move the product launch to Friday.&#10;00:04:19 Arun: Agreed. I will finish the QA checks by Thursday."
              value={transcriptText}
              onChange={(e) => setTranscriptText(e.target.value)}
              disabled={isSubmitting}
              className="w-full font-mono text-xs p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sky-500 leading-relaxed"
            />
            <p className="text-[11px] text-slate-500">
              Tip: Standard timestamps (e.g. 00:04:12) or Speaker: Text lines are automatically parsed into indexed segments.
            </p>
          </div>
        )}

        {/* Mode 2: Audio Upload */}
        {mode === "audio" && (
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">
              Audio Recording File <span className="text-rose-400">*</span>
            </label>

            <div className="p-8 border-2 border-dashed border-slate-800 hover:border-slate-700 rounded-2xl bg-slate-950/60 flex flex-col items-center justify-center space-y-3 cursor-pointer">
              <UploadCloud className="w-10 h-10 text-slate-500" />
              <div className="text-center">
                <p className="text-sm font-medium text-slate-300">
                  {audioFile ? audioFile.name : "Choose an audio file or drag and drop"}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Supports .mp3, .wav, .m4a, .ogg up to 100MB
                </p>
              </div>

              <input
                type="file"
                accept=".mp3,.wav,.m4a,.ogg,.webm,.flac"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setAudioFile(e.target.files[0]);
                  }
                }}
                disabled={isSubmitting}
                className="text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-sky-500/10 file:text-sky-400 hover:file:bg-sky-500/20"
              />
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs text-slate-500 flex items-center space-x-1.5">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>Guarded with prompt-injection boundary defenses</span>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full sm:w-auto px-6 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white shadow-lg shadow-sky-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>{submitStage || "Processing..."}</span>
              </>
            ) : (
              <>
                <span>Ingest & Extract Intelligence</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
