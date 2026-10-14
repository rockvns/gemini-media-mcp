"use client";

import { useState } from "react";
import { UserCheck, Plus, X, Upload } from "lucide-react";

interface CharacterRefPickerProps {
  paths: string[];
  onChange: (paths: string[]) => void;
  maxCount?: number;
}

export function CharacterRefPicker({ paths, onChange, maxCount = 3 }: CharacterRefPickerProps) {
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    if (paths.length >= maxCount) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.success) {
        onChange([...paths, data.filePath]);
      } else {
        alert(data.error || "Upload failed");
      }
    } catch (e: any) {
      alert(e?.message || "Upload error");
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = (index: number) => {
    const updated = [...paths];
    updated.splice(index, 1);
    onChange(updated);
  };

  return (
    <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-cyan-400" />
          <h4 className="text-sm font-semibold text-zinc-100">Character References</h4>
        </div>
        <span className="text-xs text-zinc-400">
          {paths.length} / {maxCount} references
        </span>
      </div>

      <p className="text-xs text-zinc-400">
        Attach character photos to anchor facial identity and costume consistency across Veo 3.1 video renders.
      </p>

      <div className="flex flex-wrap gap-3 pt-1">
        {paths.map((p, idx) => (
          <div
            key={idx}
            className="relative w-20 h-20 rounded-xl overflow-hidden border border-cyan-500/40 bg-[#0c0e18] group"
          >
            {/* If path points to uploads, construct api preview url */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={
                p.includes("outputs")
                  ? `/api/media/${p.split("outputs")[1].replace(/^[/\\]+/, "").replace(/\\/g, "/")}`
                  : p
              }
              alt={`Character ${idx + 1}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLElement).style.display = "none";
              }}
            />
            <button
              type="button"
              onClick={() => handleRemove(idx)}
              className="absolute top-1 right-1 p-1 rounded-full bg-black/80 text-white hover:bg-red-600 transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
            <div className="absolute bottom-0 inset-x-0 bg-black/70 text-[9px] text-center text-zinc-300 py-0.5 truncate px-1">
              Ref {idx + 1}
            </div>
          </div>
        ))}

        {paths.length < maxCount && (
          <label className="w-20 h-20 rounded-xl border border-dashed border-[#2b3352] hover:border-cyan-500/60 bg-[#0c0e18] flex flex-col items-center justify-center cursor-pointer transition-colors group">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
              }}
            />
            {uploading ? (
              <span className="text-[10px] text-cyan-400 animate-pulse">Adding...</span>
            ) : (
              <>
                <Plus className="w-5 h-5 text-zinc-400 group-hover:text-cyan-400 transition-colors" />
                <span className="text-[10px] text-zinc-400 mt-1">Add Ref</span>
              </>
            )}
          </label>
        )}
      </div>
    </div>
  );
}

