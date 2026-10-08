"use client";

import { useState } from "react";
import { X, Copy, Check, Download, FileText, Code2, Layers } from "lucide-react";
import { exportMeeting } from "@/lib/api";

interface ExportModalProps {
  meetingId: string;
  meetingTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExportModal({
  meetingId,
  meetingTitle,
  isOpen,
  onClose,
}: ExportModalProps) {
  const [format, setFormat] = useState<"markdown" | "json" | "jira">("markdown");
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  // Fetch export format content when opened or format changed
  const loadFormat = async (selectedFmt: "markdown" | "json" | "jira") => {
    setFormat(selectedFmt);
    setLoading(true);
    setCopied(false);
    try {
      const res = await exportMeeting(meetingId, selectedFmt);
      setContent(res.content);
    } catch {
      setContent("Failed to load export format.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const handleDownload = () => {
    const ext = format === "markdown" ? "md" : "json";
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${meetingTitle.toLowerCase().replace(/\s+/g, "-")}-export.${ext}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="glass-panel w-full max-w-2xl rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
        {/* Header */}
        <div className="p-4 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">
              Export Meeting Intelligence
            </h3>
            <p className="text-xs text-slate-400">{meetingTitle}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Format Selector Tabs */}
        <div className="p-3 bg-slate-950/60 border-b border-slate-800 flex items-center space-x-2">
          <button
            onClick={() => loadFormat("markdown")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              format === "markdown"
                ? "bg-sky-500/10 text-sky-400 border border-sky-500/20"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Markdown</span>
          </button>

          <button
            onClick={() => loadFormat("jira")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              format === "jira"
                ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Jira Issues Payload</span>
          </button>

          <button
            onClick={() => loadFormat("json")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              format === "json"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "text-slate-400 hover:text-white hover:bg-slate-900"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Structured JSON</span>
          </button>
        </div>

        {/* Content Box */}
        <div className="p-4">
          <div className="relative">
            <textarea
              readOnly
              rows={12}
              value={loading ? "Generating formatted export..." : content}
              className="w-full font-mono text-xs p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 focus:outline-none resize-none"
            />
          </div>
        </div>

        {/* Footer actions */}
        <div className="p-4 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            Formatted for instant sharing and tracking
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Content</span>
                </>
              )}
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-sky-500 hover:bg-sky-400 text-white shadow-md shadow-sky-500/20 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download File</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
