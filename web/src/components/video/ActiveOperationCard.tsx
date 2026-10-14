"use client";

import { useState, useEffect } from "react";
import { Loader2, CheckCircle2, AlertTriangle, RefreshCw, Copy, Check, Download, Play } from "lucide-react";

export interface OperationData {
  operation_name: string;
  media_type?: string;
  model: string;
  prompt: string;
  status: "IN_PROGRESS" | "COMPLETED" | "FAILED" | string;
  created_at: string;
  updated_at?: string;
  output_path?: string;
  error?: string;
}

interface ActiveOperationCardProps {
  operation: OperationData;
  onUpdated?: (updated: OperationData) => void;
  autoPoll?: boolean;
}

export function ActiveOperationCard({ operation, onUpdated, autoPoll = true }: ActiveOperationCardProps) {
  const [op, setOp] = useState<OperationData>(operation);
  const [isPolling, setIsPolling] = useState(false);
  const [copied, setCopied] = useState(false);
  const [elapsed, setElapsed] = useState<number>(0);

  // Keep local state synced if parent changes
  useEffect(() => {
    setOp(operation);
  }, [operation]);

  // Elapsed timer calculation
  useEffect(() => {
    const calcElapsed = () => {
      if (!op.created_at) return;
      const start = new Date(op.created_at).getTime();
      const now = Date.now();
      setElapsed(Math.max(0, Math.floor((now - start) / 1000)));
    };

    calcElapsed();
    if (op.status === "IN_PROGRESS") {
      const timer = setInterval(calcElapsed, 1000);
      return () => clearInterval(timer);
    }
  }, [op.created_at, op.status]);

  // Background auto-polling for in-progress operations
  useEffect(() => {
    if (!autoPoll || op.status !== "IN_PROGRESS") return;

    const interval = setInterval(async () => {
      await pollStatus();
    }, 8000);

    return () => clearInterval(interval);
  }, [autoPoll, op.status, op.operation_name]);

  const pollStatus = async () => {
    if (isPolling) return;
    setIsPolling(true);
    try {
      const res = await fetch("/api/mcp/operations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operation_name: op.operation_name }),
      });
      const data = await res.json();
      if (data.success && data.operation) {
        setOp(data.operation);
        if (onUpdated) onUpdated(data.operation);
      }
    } catch (e) {
      console.error("Polling error:", e);
    } finally {
      setIsPolling(false);
    }
  };

  const copyId = () => {
    navigator.clipboard.writeText(op.operation_name);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getMediaUrl = (absPath?: string) => {
    if (!absPath) return null;
    const parts = absPath.split(/outputs[/\\]/);
    if (parts.length > 1) {
      return `/api/media/${parts[1].replace(/\\/g, "/")}`;
    }
    return null;
  };

  const mediaUrl = getMediaUrl(op.output_path);

  return (
    <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-4 shadow-xl">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1b2034] pb-3">
        <div className="flex items-center gap-3">
          {op.status === "IN_PROGRESS" && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-violet-500/10 border border-violet-500/30 text-violet-400 text-xs font-semibold">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Rendering Video ({elapsed}s)</span>
            </div>
          )}
          {op.status === "COMPLETED" && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Completed ({elapsed}s)</span>
            </div>
          )}
          {op.status === "FAILED" && (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Generation Failed</span>
            </div>
          )}
          <span className="text-xs font-mono text-zinc-400 bg-[#090b14] px-2 py-0.5 rounded border border-[#1f253d]">
            {op.model}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={copyId}
            className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-zinc-200 px-2 py-1 rounded bg-[#090b14] border border-[#1f253d] transition-colors"
            title="Copy Operation ID"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span className="truncate max-w-[120px]">{op.operation_name}</span>
          </button>

          {op.status === "IN_PROGRESS" && (
            <button
              onClick={pollStatus}
              disabled={isPolling}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-violet-600/20 text-violet-300 hover:bg-violet-600/30 border border-violet-500/30 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? "animate-spin" : ""}`} />
              <span>Poll Status</span>
            </button>
          )}
        </div>
      </div>

      {/* Prompt preview */}
      <p className="text-xs text-zinc-300 line-clamp-2 italic bg-[#0a0c16] p-2.5 rounded-xl border border-[#1b2034]">
        &quot;{op.prompt}&quot;
      </p>

      {/* Video Player when completed */}
      {op.status === "COMPLETED" && mediaUrl && (
        <div className="space-y-3">
          <div className="relative rounded-xl overflow-hidden border border-violet-500/40 bg-black shadow-lg aspect-video max-h-[380px] mx-auto flex items-center justify-center">
            <video
              src={mediaUrl}
              controls
              autoPlay
              loop
              playsInline
              className="w-full h-full object-contain"
            />
          </div>
          <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
            <span className="truncate max-w-[70%]">{op.output_path}</span>
            <a
              href={mediaUrl}
              download
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-medium shadow transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download MP4</span>
            </a>
          </div>
        </div>
      )}

      {/* Error display */}
      {op.status === "FAILED" && op.error && (
        <div className="p-3 bg-red-950/30 border border-red-800/50 rounded-xl text-xs text-red-300 space-y-1">
          <div className="font-semibold flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span>Diagnostics & Error Details</span>
          </div>
          <pre className="whitespace-pre-wrap font-mono text-[11px] text-red-200/90 max-h-36 overflow-y-auto">
            {op.error}
          </pre>
        </div>
      )}
    </div>
  );
}

