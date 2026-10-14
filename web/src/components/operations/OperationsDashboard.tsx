"use client";

import { useState, useEffect } from "react";
import {
  Activity,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Clock,
  Filter,
} from "lucide-react";
import { ActiveOperationCard, OperationData } from "@/components/video/ActiveOperationCard";

export function OperationsDashboard() {
  const [operations, setOperations] = useState<OperationData[]>([]);
  const [filter, setFilter] = useState<string>("ALL");
  const [isLoading, setIsLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchOperations = async () => {
    try {
      const url = filter === "ALL" ? "/api/mcp/operations" : `/api/mcp/operations?filter=${filter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setOperations(data.operations || []);
      }
    } catch (e) {
      console.error("Failed to fetch operations:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOperations();
  }, [filter]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchOperations, 8000);
    return () => clearInterval(interval);
  }, [autoRefresh, filter]);

  const inProgressCount = operations.filter((o) => o.status === "IN_PROGRESS").length;
  const completedCount = operations.filter((o) => o.status === "COMPLETED").length;
  const failedCount = operations.filter((o) => o.status === "FAILED").length;

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1f2438] pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Activity className="w-8 h-8 text-violet-400" />
            <span>Operations & Task Monitor</span>
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Real-time tracking of asynchronous video renders and long-running generation jobs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-zinc-300 bg-[#121524] px-3 py-2 rounded-xl border border-[#21273f] cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-3.5 h-3.5 rounded text-violet-600"
            />
            <span>Auto Refresh (8s)</span>
          </label>

          <button
            onClick={() => {
              setIsLoading(true);
              fetchOperations();
            }}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white shadow transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-4 space-y-1">
          <div className="text-xs text-zinc-400">Total Tracked</div>
          <div className="text-2xl font-bold text-white">{operations.length}</div>
        </div>

        <div className="bg-[#121524] border border-violet-500/30 rounded-2xl p-4 space-y-1">
          <div className="text-xs text-violet-400 flex items-center gap-1.5">
            <Loader2 className="w-3 h-3 animate-spin" /> In Progress
          </div>
          <div className="text-2xl font-bold text-violet-300">{inProgressCount}</div>
        </div>

        <div className="bg-[#121524] border border-emerald-500/30 rounded-2xl p-4 space-y-1">
          <div className="text-xs text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3" /> Completed
          </div>
          <div className="text-2xl font-bold text-emerald-300">{completedCount}</div>
        </div>

        <div className="bg-[#121524] border border-red-500/30 rounded-2xl p-4 space-y-1">
          <div className="text-xs text-red-400 flex items-center gap-1.5">
            <AlertTriangle className="w-3 h-3" /> Failed
          </div>
          <div className="text-2xl font-bold text-red-300">{failedCount}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-[#1f2438] pb-3">
        <Filter className="w-4 h-4 text-zinc-400" />
        <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mr-2">Filter:</span>
        {["ALL", "IN_PROGRESS", "COMPLETED", "FAILED"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              filter === f
                ? "bg-violet-600 text-white shadow-sm"
                : "bg-[#111422] text-zinc-400 hover:text-zinc-200 border border-[#21273f]"
            }`}
          >
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Operations List */}
      {operations.length === 0 ? (
        <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-12 text-center space-y-3">
          <Clock className="w-10 h-10 text-zinc-500 mx-auto" />
          <h3 className="text-sm font-semibold text-zinc-300">No Tracked Operations Found</h3>
          <p className="text-xs text-zinc-500 max-w-sm mx-auto">
            Jobs submitted from the Video Studio will automatically appear here with real-time status and output download links.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {operations.map((op) => (
            <ActiveOperationCard
              key={op.operation_name}
              operation={op}
              onUpdated={(updated) => {
                setOperations((prev) =>
                  prev.map((item) =>
                    item.operation_name === updated.operation_name ? updated : item
                  )
                );
              }}
              autoPoll={op.status === "IN_PROGRESS"}
            />
          ))}
        </div>
      )}
    </div>
  );
}

