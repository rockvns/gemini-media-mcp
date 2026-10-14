"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  FolderHeart,
  Video,
  Image as ImageIcon,
  Download,
  Eye,
  ArrowRight,
  Wand2,
  X,
  Search,
  Calendar,
  HardDrive,
  RefreshCw,
} from "lucide-react";
import { MediaAsset } from "@/lib/constants";

export function GalleryGrid() {
  const router = useRouter();
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [typeFilter, setTypeFilter] = useState<"all" | "video" | "image">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState<MediaAsset | null>(null);

  const fetchAssets = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/gallery?type=${typeFilter}`);
      if (res.ok) {
        const data = await res.json();
        setAssets(data.assets || []);
      }
    } catch (e) {
      console.error("Gallery fetch error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [typeFilter]);

  const formatBytes = (bytes: number) => {
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  const filteredAssets = assets.filter((a) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      a.filename.toLowerCase().includes(q) ||
      (a.prompt && a.prompt.toLowerCase().includes(q)) ||
      (a.model && a.model.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1f2438] pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <FolderHeart className="w-8 h-8 text-fuchsia-400" />
            <span>Media Gallery & Assets</span>
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Browse, play, and inspect all generated videos and high-resolution images from outputs.
          </p>
        </div>

        <button
          onClick={fetchAssets}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-[#121524] hover:bg-[#1a1f33] text-zinc-200 border border-[#21273f] transition-all self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Type Filter Tabs */}
        <div className="flex items-center bg-[#111422] p-1 rounded-xl border border-[#21273f]">
          <button
            onClick={() => setTypeFilter("all")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              typeFilter === "all" ? "bg-fuchsia-600 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            All Media ({assets.length})
          </button>
          <button
            onClick={() => setTypeFilter("video")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              typeFilter === "video" ? "bg-fuchsia-600 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Video className="w-3.5 h-3.5" />
            <span>Videos</span>
          </button>
          <button
            onClick={() => setTypeFilter("image")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              typeFilter === "image" ? "bg-fuchsia-600 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            <span>Images</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by prompt or filename..."
            className="w-full pl-9 pr-3.5 py-2 bg-[#111422] border border-[#21273f] rounded-xl text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-fuchsia-500"
          />
        </div>
      </div>

      {/* Grid */}
      {filteredAssets.length === 0 ? (
        <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-12 text-center space-y-3">
          <FolderHeart className="w-10 h-10 text-zinc-500 mx-auto" />
          <h3 className="text-sm font-semibold text-zinc-300">No Media Files Found</h3>
          <p className="text-xs text-zinc-500 max-w-sm mx-auto">
            Images and videos generated in the studios will automatically be archived and displayed here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {filteredAssets.map((asset) => {
            const isVideo = asset.type === "video";
            return (
              <div
                key={asset.relativePath}
                className="bg-[#121524] border border-[#21273f] rounded-2xl overflow-hidden flex flex-col group hover:border-zinc-600 transition-all shadow-lg"
              >
                {/* Media Preview Box */}
                <div
                  onClick={() => setSelectedAsset(asset)}
                  className="relative aspect-video bg-black flex items-center justify-center cursor-pointer overflow-hidden"
                >
                  {isVideo ? (
                    <video
                      src={asset.url}
                      muted
                      playsInline
                      preload="metadata"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={asset.url}
                      alt={asset.filename}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  )}

                  {/* Type Badge */}
                  <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider backdrop-blur-md bg-black/60 text-white border border-white/10 flex items-center gap-1">
                    {isVideo ? <Video className="w-3 h-3 text-violet-400" /> : <ImageIcon className="w-3 h-3 text-cyan-400" />}
                    <span>{isVideo ? "MP4" : "PNG"}</span>
                  </div>

                  {/* Hover overlay with action */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="px-3 py-1.5 rounded-xl bg-white/20 backdrop-blur-sm text-white text-xs font-semibold flex items-center gap-1.5 shadow">
                      <Eye className="w-3.5 h-3.5" /> Inspect
                    </span>
                  </div>
                </div>

                {/* Info Card */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div>
                    <div className="text-xs font-semibold text-zinc-200 truncate" title={asset.filename}>
                      {asset.filename}
                    </div>
                    {asset.prompt && (
                      <p className="text-[11px] text-zinc-400 italic line-clamp-2 mt-1">
                        &quot;{asset.prompt}&quot;
                      </p>
                    )}
                  </div>

                  <div className="pt-2 border-t border-[#1b2034] flex items-center justify-between text-[10px] text-zinc-500">
                    <span className="flex items-center gap-1">
                      <HardDrive className="w-3 h-3" /> {formatBytes(asset.size)}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> {new Date(asset.createdAt).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-1 gap-2">
                    <a
                      href={asset.url}
                      download
                      className="p-1.5 rounded-lg bg-[#191d30] hover:bg-zinc-700 text-zinc-300 transition-colors"
                      title="Download"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>

                    {!isVideo && (
                      <button
                        onClick={() => router.push(`/video?keyframe=${encodeURIComponent(asset.absolutePath)}`)}
                        className="flex-1 py-1 px-2 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 text-[10px] font-semibold flex items-center justify-center gap-1"
                      >
                        <span>To Video</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Lightbox Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="max-w-4xl w-full bg-[#111320] border border-[#262c47] rounded-2xl overflow-hidden flex flex-col shadow-2xl">
            {/* Header */}
            <div className="p-4 border-b border-[#21263d] flex items-center justify-between bg-[#141829]">
              <div className="flex items-center gap-2 truncate max-w-lg">
                {selectedAsset.type === "video" ? (
                  <Video className="w-4 h-4 text-violet-400" />
                ) : (
                  <ImageIcon className="w-4 h-4 text-cyan-400" />
                )}
                <span className="text-sm font-semibold text-zinc-200 truncate">
                  {selectedAsset.filename}
                </span>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-[#1f243b]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Media Viewer */}
            <div className="p-4 bg-black flex items-center justify-center max-h-[70vh]">
              {selectedAsset.type === "video" ? (
                <video
                  src={selectedAsset.url}
                  controls
                  autoPlay
                  loop
                  playsInline
                  className="max-h-[65vh] w-auto max-w-full rounded-lg shadow-2xl"
                />
              ) : (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={selectedAsset.url}
                  alt={selectedAsset.filename}
                  className="max-h-[65vh] w-auto max-w-full object-contain rounded-lg shadow-2xl"
                />
              )}
            </div>

            {/* Metadata Footer */}
            <div className="p-4 border-t border-[#21263d] bg-[#141829] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="space-y-0.5 truncate">
                {selectedAsset.prompt && (
                  <p className="text-zinc-200 font-medium truncate max-w-md">
                    &quot;{selectedAsset.prompt}&quot;
                  </p>
                )}
                <p className="text-zinc-400 font-mono text-[11px]">
                  Size: {formatBytes(selectedAsset.size)} • Path: {selectedAsset.absolutePath}
                </p>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-auto">
                {selectedAsset.type === "image" && (
                  <button
                    onClick={() => {
                      router.push(`/video?keyframe=${encodeURIComponent(selectedAsset.absolutePath)}`);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-violet-600/30 text-violet-300 border border-violet-500/40 hover:bg-violet-600/40 font-semibold transition-colors"
                  >
                    <span>Use as Keyframe</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
                <a
                  href={selectedAsset.url}
                  download
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-fuchsia-600 hover:bg-fuchsia-500 text-white font-semibold transition-colors"
                >
                  <Download className="w-4 h-4" /> Download
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

