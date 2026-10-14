"use client";

import { useState } from "react";
import { Upload, X, Image as ImageIcon, Sparkles, Layers } from "lucide-react";

export type KeyframeMode = "none" | "single" | "pair";

interface KeyframeUploaderProps {
  mode: KeyframeMode;
  onModeChange: (mode: KeyframeMode) => void;
  firstFramePath: string;
  onFirstFrameChange: (path: string, previewUrl?: string) => void;
  lastFramePath: string;
  onLastFrameChange: (path: string, previewUrl?: string) => void;
  firstFramePreview?: string;
  lastFramePreview?: string;
}

export function KeyframeUploader({
  mode,
  onModeChange,
  firstFramePath,
  onFirstFrameChange,
  lastFramePath,
  onLastFrameChange,
  firstFramePreview,
  lastFramePreview,
}: KeyframeUploaderProps) {
  const [uploadingFirst, setUploadingFirst] = useState(false);
  const [uploadingLast, setUploadingLast] = useState(false);

  const handleFileUpload = async (file: File, isFirst: boolean) => {
    const formData = new FormData();
    formData.append("file", file);

    if (isFirst) setUploadingFirst(true);
    else setUploadingLast(true);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        if (isFirst) {
          onFirstFrameChange(data.filePath, data.url);
        } else {
          onLastFrameChange(data.filePath, data.url);
        }
      } else {
        alert(data.error || "Upload failed");
      }
    } catch (e: any) {
      alert(e?.message || "Upload error");
    } finally {
      if (isFirst) setUploadingFirst(false);
      else setUploadingLast(false);
    }
  };

  return (
    <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-violet-400" />
          <h4 className="text-sm font-semibold text-zinc-100">Keyframe Animation Modes</h4>
        </div>

        {/* Segmented control */}
        <div className="flex items-center bg-[#090b14] p-1 rounded-xl border border-[#21273f]">
          <button
            type="button"
            onClick={() => onModeChange("none")}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
              mode === "none"
                ? "bg-violet-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            0 Frames (Text)
          </button>
          <button
            type="button"
            onClick={() => onModeChange("single")}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
              mode === "single"
                ? "bg-violet-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            1 Frame (Start)
          </button>
          <button
            type="button"
            onClick={() => onModeChange("pair")}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-all ${
              mode === "pair"
                ? "bg-violet-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            2 Frames (Interpolate)
          </button>
        </div>
      </div>

      {mode === "none" && (
        <p className="text-xs text-zinc-400">
          Pure text-to-video prompt. Veo 3.1 synthesizes the full 8-second motion and audio from your description.
        </p>
      )}

      {mode !== "none" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          {/* First Keyframe */}
          <div className="space-y-2">
            <span className="text-xs font-medium text-zinc-300 flex items-center justify-between">
              <span>Opening Keyframe (Start)</span>
              {firstFramePath && (
                <button
                  type="button"
                  onClick={() => onFirstFrameChange("", "")}
                  className="text-red-400 hover:text-red-300 text-[11px]"
                >
                  Clear
                </button>
              )}
            </span>

            {firstFramePreview ? (
              <div className="relative aspect-video rounded-xl overflow-hidden border border-violet-500/40 group">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={firstFramePreview}
                  alt="Start Keyframe"
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => onFirstFrameChange("", "")}
                  className="absolute top-2 right-2 p-1 rounded-full bg-black/70 text-white hover:bg-black transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center aspect-video rounded-xl border border-dashed border-[#2b3352] hover:border-violet-500/60 bg-[#0c0e18] cursor-pointer transition-colors p-4 text-center">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFileUpload(f, true);
                  }}
                />
                {uploadingFirst ? (
                  <div className="text-xs text-violet-400 animate-pulse">Uploading keyframe...</div>
                ) : (
                  <>
                    <Upload className="w-6 h-6 text-zinc-400 mb-1.5" />
                    <span className="text-xs font-medium text-zinc-200">Upload Start Keyframe</span>
                    <span className="text-[10px] text-zinc-500 mt-0.5">PNG, JPG, or WebP</span>
                  </>
                )}
              </label>
            )}
            <input
              type="text"
              value={firstFramePath}
              onChange={(e) => onFirstFrameChange(e.target.value)}
              placeholder="Or enter file path (e.g. outputs/frame1.png)"
              className="w-full px-3 py-1.5 bg-[#090b14] border border-[#21273f] rounded-lg text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500"
            />
          </div>

          {/* Second Keyframe (for pair mode) */}
          {mode === "pair" && (
            <div className="space-y-2">
              <span className="text-xs font-medium text-zinc-300 flex items-center justify-between">
                <span>Ending Keyframe (End)</span>
                {lastFramePath && (
                  <button
                    type="button"
                    onClick={() => onLastFrameChange("", "")}
                    className="text-red-400 hover:text-red-300 text-[11px]"
                  >
                    Clear
                  </button>
                )}
              </span>

              {lastFramePreview ? (
                <div className="relative aspect-video rounded-xl overflow-hidden border border-violet-500/40 group">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={lastFramePreview}
                    alt="End Keyframe"
                    className="w-full h-full object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => onLastFrameChange("", "")}
                    className="absolute top-2 right-2 p-1 rounded-full bg-black/70 text-white hover:bg-black transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <label className="flex flex-col items-center justify-center aspect-video rounded-xl border border-dashed border-[#2b3352] hover:border-violet-500/60 bg-[#0c0e18] cursor-pointer transition-colors p-4 text-center">
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleFileUpload(f, false);
                    }}
                  />
                  {uploadingLast ? (
                    <div className="text-xs text-violet-400 animate-pulse">Uploading keyframe...</div>
                  ) : (
                    <>
                      <Upload className="w-6 h-6 text-zinc-400 mb-1.5" />
                      <span className="text-xs font-medium text-zinc-200">Upload End Keyframe</span>
                      <span className="text-[10px] text-zinc-500 mt-0.5">Veo will interpolate smoothly</span>
                    </>
                  )}
                </label>
              )}
              <input
                type="text"
                value={lastFramePath}
                onChange={(e) => onLastFrameChange(e.target.value)}
                placeholder="Or enter file path (e.g. outputs/frame2.png)"
                className="w-full px-3 py-1.5 bg-[#090b14] border border-[#21273f] rounded-lg text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

