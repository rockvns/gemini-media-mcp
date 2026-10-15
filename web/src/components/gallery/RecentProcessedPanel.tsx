"use client";

import { useState, useEffect } from "react";
import {
  Sparkles,
  Layers,
  UserPlus,
  RefreshCw,
  Film,
  Image as ImageIcon,
  Check,
  ExternalLink,
} from "lucide-react";
import { MediaAsset } from "@/lib/constants";

interface RecentProcessedPanelProps {
  currentModel: string;
  supportsKeyframes?: boolean;
  supportsCharacters?: boolean;
  maxCharacterCount?: number;
  currentCharacterCount?: number;
  onAddCharacter?: (filePath: string) => void;
  onSetKeyframe?: (frameType: "first" | "last", filePath: string, previewUrl: string) => void;
  onUseAsEditSource?: (filePath: string, previewUrl: string) => void;
}

export function RecentProcessedPanel({
  currentModel,
  supportsKeyframes = false,
  supportsCharacters = false,
  maxCharacterCount = 3,
  currentCharacterCount = 0,
  onAddCharacter,
  onSetKeyframe,
  onUseAsEditSource,
}: RecentProcessedPanelProps) {
  const [recentAssets, setRecentAssets] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const fetchRecent = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/gallery?type=all");
      if (res.ok) {
        const data = await res.json();
        const all: MediaAsset[] = data.assets || [];
        setRecentAssets(all.slice(0, 10));
      }
    } catch (e) {
      console.error("Failed to fetch recent assets:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecent();
  }, []);

  const showNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 3000);
  };

  const formatSize = (bytes: number) => {
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  const canAddMoreCharacters = supportsCharacters && currentCharacterCount < maxCharacterCount;

  return (
    <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-4 space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#21273f] pb-3">
        <div>
          <h3 className="text-xs font-bold text-zinc-100 uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Recent Media (Last 10)</span>
          </h3>
          <p className="text-[11px] text-zinc-400 mt-0.5">
            Quick-access pipeline to character & keyframe anchors
          </p>
        </div>

        <button
          type="button"
          onClick={fetchRecent}
          disabled={loading}
          title="Refresh recent media"
          className="p-1.5 rounded-lg bg-[#181c2e] hover:bg-[#20263f] text-zinc-300 hover:text-white transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
        </button>
      </div>

      {/* Action Notification Toast */}
      {actionNotice && (
        <div className="p-2.5 bg-emerald-950/60 border border-emerald-600/50 rounded-xl text-xs text-emerald-200 flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="truncate">{actionNotice}</span>
        </div>
      )}

      {/* Media Items */}
      {recentAssets.length === 0 ? (
        <div className="py-8 text-center text-zinc-500 text-xs">
          {loading ? "Scanning outputs folder..." : "No processed media found yet."}
        </div>
      ) : (
        <div className="space-y-3 max-h-[540px] overflow-y-auto pr-1">
          {recentAssets.map((asset) => {
            const isVideo = asset.type === "video";
            const isImage = !isVideo;

            return (
              <div
                key={asset.relativePath}
                className="bg-[#090b14] border border-[#1e2338] hover:border-zinc-700 rounded-xl p-2.5 transition-all space-y-2.5 group"
              >
                <div className="flex gap-3">
                  {/* Thumbnail */}
                  <div className="relative w-16 h-16 rounded-lg overflow-hidden bg-black/50 shrink-0 border border-zinc-800">
                    {isVideo ? (
                      <video
                        src={asset.url}
                        className="w-full h-full object-cover"
                        preload="metadata"
                      />
                    ) : (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={asset.url}
                        alt={asset.filename}
                        className="w-full h-full object-cover"
                      />
                    )}
                    <span className="absolute top-1 left-1 px-1 py-0.2 rounded bg-black/70 text-[9px] font-mono text-zinc-300 uppercase">
                      {isVideo ? "VID" : "IMG"}
                    </span>
                  </div>

                  {/* Metadata */}
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-zinc-200 truncate" title={asset.filename}>
                      {asset.filename}
                    </div>
                    <div className="text-[11px] text-zinc-400 line-clamp-1 mt-0.5" title={asset.prompt || ""}>
                      {asset.prompt || asset.model || "Processed Media"}
                    </div>
                    <div className="text-[10px] text-zinc-500 mt-1 flex items-center gap-2">
                      <span>{formatSize(asset.size)}</span>
                      {asset.aspectRatio && <span>• {asset.aspectRatio}</span>}
                      {asset.resolution && <span>• {asset.resolution}</span>}
                    </div>
                  </div>
                </div>

                {/* Quick Action Buttons (Only enabled when model allows) */}
                {isImage && (
                  <div className="flex flex-wrap gap-1.5 pt-1 border-t border-[#1a1f33]">
                    {/* Add as Character Anchor */}
                    {onAddCharacter && (
                      <button
                        type="button"
                        disabled={!canAddMoreCharacters}
                        onClick={() => {
                          onAddCharacter(asset.absolutePath);
                          showNotice(`Added "${asset.filename}" to Character References`);
                        }}
                        className={`px-2 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1 transition-all ${
                          canAddMoreCharacters
                            ? "bg-cyan-950/70 text-cyan-300 border border-cyan-700/50 hover:bg-cyan-900"
                            : "bg-zinc-900/50 text-zinc-600 border border-zinc-800 cursor-not-allowed"
                        }`}
                        title={
                          !supportsCharacters
                            ? `Model '${currentModel}' does not support character attachments`
                            : currentCharacterCount >= maxCharacterCount
                            ? `Maximum character limit (${maxCharacterCount}) reached`
                            : "Attach as character reference"
                        }
                      >
                        <UserPlus className="w-3 h-3" />
                        <span>Character Ref</span>
                      </button>
                    )}

                    {/* Set as Start Keyframe */}
                    {onSetKeyframe && (
                      <button
                        type="button"
                        disabled={!supportsKeyframes}
                        onClick={() => {
                          onSetKeyframe("first", asset.absolutePath, asset.url);
                          showNotice(`Set "${asset.filename}" as Start Keyframe`);
                        }}
                        className={`px-2 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1 transition-all ${
                          supportsKeyframes
                            ? "bg-violet-950/70 text-violet-300 border border-violet-700/50 hover:bg-violet-900"
                            : "bg-zinc-900/50 text-zinc-600 border border-zinc-800 cursor-not-allowed"
                        }`}
                        title={
                          supportsKeyframes
                            ? "Use as Starting Keyframe (0s)"
                            : `Model '${currentModel}' does not support keyframe interpolation`
                        }
                      >
                        <Layers className="w-3 h-3" />
                        <span>Start Frame</span>
                      </button>
                    )}

                    {/* Set as End Keyframe */}
                    {onSetKeyframe && (
                      <button
                        type="button"
                        disabled={!supportsKeyframes}
                        onClick={() => {
                          onSetKeyframe("last", asset.absolutePath, asset.url);
                          showNotice(`Set "${asset.filename}" as End Keyframe`);
                        }}
                        className={`px-2 py-1 rounded-lg text-[10px] font-medium flex items-center gap-1 transition-all ${
                          supportsKeyframes
                            ? "bg-indigo-950/70 text-indigo-300 border border-indigo-700/50 hover:bg-indigo-900"
                            : "bg-zinc-900/50 text-zinc-600 border border-zinc-800 cursor-not-allowed"
                        }`}
                        title={
                          supportsKeyframes
                            ? "Use as Ending Keyframe (8s)"
                            : `Model '${currentModel}' does not support keyframe interpolation`
                        }
                      >
                        <Film className="w-3 h-3" />
                        <span>End Frame</span>
                      </button>
                    )}

                    {/* Use as Edit Source (Image Studio only) */}
                    {onUseAsEditSource && (
                      <button
                        type="button"
                        onClick={() => {
                          onUseAsEditSource(asset.absolutePath, asset.url);
                          showNotice(`Loaded "${asset.filename}" into Image Editor`);
                        }}
                        className="px-2 py-1 rounded-lg text-[10px] font-medium bg-emerald-950/70 text-emerald-300 border border-emerald-700/50 hover:bg-emerald-900 flex items-center gap-1 transition-all"
                        title="Load into Edit Studio"
                      >
                        <ImageIcon className="w-3 h-3" />
                        <span>Edit Source</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

