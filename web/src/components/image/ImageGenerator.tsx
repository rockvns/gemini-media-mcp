"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  Image as ImageIcon,
  Sliders,
  Check,
  Search,
  Layers,
  Wand2,
  Upload,
  X,
  Plus,
  Download,
  ArrowRight,
  Bookmark,
  AlertCircle,
  Eye,
} from "lucide-react";
import { IMAGE_MODELS, ASPECT_RATIOS } from "@/lib/constants";
import { RecentProcessedPanel } from "@/components/gallery/RecentProcessedPanel";

type StudioMode = "generate" | "keyframes" | "edit";

export function ImageGenerator() {
  const router = useRouter();
  const [studioMode, setStudioMode] = useState<StudioMode>("generate");

  // Common Generation state
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("gemini-nano-banana-2.1");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [imageSize, setImageSize] = useState("2K");
  const [enableGoogleSearch, setEnableGoogleSearch] = useState(false);
  const [saveAsPreference, setSaveAsPreference] = useState(false);

  // References
  const [characterPaths, setCharacterPaths] = useState<string[]>([]);
  const [referencePaths, setReferencePaths] = useState<string[]>([]);

  // Keyframes Mode state
  const [startPrompt, setStartPrompt] = useState("");
  const [endPrompt, setEndPrompt] = useState("");
  const [numKeyframes, setNumKeyframes] = useState<1 | 2>(2);

  // Edit Mode state
  const [editSourcePath, setEditSourcePath] = useState("");
  const [editSourcePreview, setEditSourcePreview] = useState("");
  const [editPrompt, setEditPrompt] = useState("");

  // Result state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [resultImages, setResultImages] = useState<{ path: string; url: string; prompt: string }[]>([]);
  const [previewModalImg, setPreviewModalImg] = useState<{ path: string; url: string; prompt: string } | null>(null);

  // Upload loaders
  const [uploadingChar, setUploadingChar] = useState(false);
  const [uploadingRef, setUploadingRef] = useState(false);
  const [uploadingEditSrc, setUploadingEditSrc] = useState(false);

  // Load saved preferences
  useEffect(() => {
    fetch("/api/mcp/preferences")
      .then((r) => r.json())
      .then((data) => {
        if (data.preferences?.image) {
          const img = data.preferences.image;
          if (img.model) setModel(img.model);
          if (img.aspect_ratio) setAspectRatio(img.aspect_ratio);
          if (img.image_size) setImageSize(img.image_size);
          if (img.enable_google_search !== undefined) setEnableGoogleSearch(img.enable_google_search);
        }
      })
      .catch(() => {});
  }, []);

  const currentModelSpec = IMAGE_MODELS[model] || IMAGE_MODELS["gemini-nano-banana-2.1"];

  const handleModelSelect = (newModelId: string) => {
    setModel(newModelId);
    const spec = IMAGE_MODELS[newModelId];
    if (spec) {
      if (!spec.supportedSizes.includes(imageSize)) {
        setImageSize(spec.supportedSizes[0]);
      }
      if (!spec.supportedAspectRatios.includes(aspectRatio)) {
        setAspectRatio(spec.supportedAspectRatios[0]);
      }
      if (!spec.supportsGoogleSearch) {
        setEnableGoogleSearch(false);
      }
      if (characterPaths.length > spec.maxCharacterReferences) {
        setCharacterPaths(characterPaths.slice(0, spec.maxCharacterReferences));
      }
    }
  };

  // File upload helper
  const handleUpload = async (file: File, type: "char" | "ref" | "editSrc") => {
    const formData = new FormData();
    formData.append("file", file);

    if (type === "char") setUploadingChar(true);
    else if (type === "ref") setUploadingRef(true);
    else setUploadingEditSrc(true);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.success) {
        if (type === "char") {
          setCharacterPaths([...characterPaths, data.filePath]);
        } else if (type === "ref") {
          setReferencePaths([...referencePaths, data.filePath]);
        } else {
          setEditSourcePath(data.filePath);
          setEditSourcePreview(data.url);
        }
      } else {
        alert(data.error || "Upload failed");
      }
    } catch (e: any) {
      alert(e?.message || "Upload error");
    } finally {
      if (type === "char") setUploadingChar(false);
      else if (type === "ref") setUploadingRef(false);
      else setUploadingEditSrc(false);
    }
  };

  const parseImagePathsFromResponse = (text: string, currentPrompt: string) => {
    // Regex looking for output image paths (e.g. outputs\xyz.png or D:\...outputs\xyz.png)
    const matches = text.match(/(?:[a-zA-Z]:[\\/])?[^\s\n\r"']+\.(?:png|jpg|jpeg|webp)/gi) || [];
    const valid = matches.filter((p) => p.includes("outputs") || p.includes("outputs/"));

    const newItems = valid.map((filePath) => {
      const parts = filePath.split(/outputs[/\\]/);
      const url = parts.length > 1 ? `/api/media/${parts[1].replace(/\\/g, "/")}` : filePath;
      return { path: filePath, url, prompt: currentPrompt };
    });

    if (newItems.length > 0) {
      setResultImages((prev) => [...newItems, ...prev]);
      setPreviewModalImg(newItems[0]);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorBanner(null);

    try {
      let toolName = "generate_image";
      let payload: Record<string, any> = {};

      if (studioMode === "generate") {
        if (!prompt.trim()) return;
        toolName = "generate_image";
        payload = {
          prompt: prompt.trim(),
          model,
          aspect_ratio: aspectRatio,
          image_size: imageSize,
          enable_google_search: currentModelSpec.supportsGoogleSearch ? enableGoogleSearch : false,
          save_as_preference: saveAsPreference,
        };
        if (characterPaths.length > 0) payload.character_paths = characterPaths;
        if (referencePaths.length > 0) payload.reference_image_paths = referencePaths;
      } else if (studioMode === "keyframes") {
        if (!startPrompt.trim()) return;
        toolName = "generate_keyframes";
        payload = {
          start_prompt: startPrompt.trim(),
          end_prompt: numKeyframes === 2 ? endPrompt.trim() : undefined,
          num_frames: numKeyframes,
          model,
          aspect_ratio: aspectRatio,
          image_size: imageSize,
        };
        if (characterPaths.length > 0) payload.character_paths = characterPaths;
      } else if (studioMode === "edit") {
        if (!editPrompt.trim() || !editSourcePath) {
          setErrorBanner("Please select a source image and describe the modifications.");
          setIsSubmitting(false);
          return;
        }
        toolName = "edit_image";
        payload = {
          prompt: editPrompt.trim(),
          image_path: editSourcePath,
          model,
          aspect_ratio: aspectRatio,
          image_size: imageSize,
        };
      }

      const res = await fetch("/api/mcp/tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool: toolName, args: payload }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setErrorBanner(data.content || data.error || "Generation error");
        setIsSubmitting(false);
        return;
      }

      const activePrompt =
        studioMode === "generate"
          ? prompt
          : studioMode === "keyframes"
          ? `${startPrompt} -> ${endPrompt}`
          : editPrompt;

      parseImagePathsFromResponse(data.content, activePrompt);
    } catch (err: any) {
      setErrorBanner(err?.message || "Generation error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1f2438] pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <ImageIcon className="w-8 h-8 text-cyan-400" />
            <span>Image Studio (Nano Banana)</span>
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Gemini Nano Banana 2.1 & 3 Pro with 4K resolution, 10 aspect ratios, Google Search grounding, and keyframe pairs.
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex items-center bg-[#111422] p-1 rounded-xl border border-[#21273f]">
          <button
            type="button"
            onClick={() => setStudioMode("generate")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-all ${
              studioMode === "generate"
                ? "bg-cyan-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate</span>
          </button>
          <button
            type="button"
            onClick={() => setStudioMode("keyframes")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-all ${
              studioMode === "keyframes"
                ? "bg-cyan-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Keyframes (1 or 2)</span>
          </button>
          <button
            type="button"
            onClick={() => setStudioMode("edit")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition-all ${
              studioMode === "edit"
                ? "bg-cyan-600 text-white shadow-sm"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>Image Editor</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form: 7 columns */}
        <form onSubmit={handleGenerate} className="lg:col-span-7 space-y-6">
          {/* Mode 1: Standard Generate Prompt */}
          {studioMode === "generate" && (
            <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-cyan-400" /> Image Prompt
                </label>
                <span className="text-xs text-zinc-500">{prompt.length} chars</span>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your subject, lighting, composition, photographic style, textures, and typography..."
                rows={4}
                required
                className="w-full px-4 py-3 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
          )}

          {/* Mode 2: Keyframe Generator */}
          {studioMode === "keyframes" && (
            <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                    Keyframe Pair Configuration
                  </h4>
                </div>
                <div className="flex items-center gap-1 bg-[#090b14] p-1 rounded-lg border border-[#21273f]">
                  <button
                    type="button"
                    onClick={() => setNumKeyframes(1)}
                    className={`px-2.5 py-1 text-xs rounded font-medium ${
                      numKeyframes === 1 ? "bg-cyan-600 text-white" : "text-zinc-400"
                    }`}
                  >
                    1 Frame (Start)
                  </button>
                  <button
                    type="button"
                    onClick={() => setNumKeyframes(2)}
                    className={`px-2.5 py-1 text-xs rounded font-medium ${
                      numKeyframes === 2 ? "bg-cyan-600 text-white" : "text-zinc-400"
                    }`}
                  >
                    2 Frames (Consistent Pair)
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs text-zinc-300 font-medium block mb-1">Opening Scene Prompt (Start)</label>
                <textarea
                  value={startPrompt}
                  onChange={(e) => setStartPrompt(e.target.value)}
                  placeholder="Describe opening shot / initial posture / environment..."
                  rows={2}
                  required
                  className="w-full px-3.5 py-2.5 bg-[#090b14] border border-[#232943] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {numKeyframes === 2 && (
                <div>
                  <label className="text-xs text-zinc-300 font-medium block mb-1">Ending Scene Prompt (Final)</label>
                  <textarea
                    value={endPrompt}
                    onChange={(e) => setEndPrompt(e.target.value)}
                    placeholder="Describe ending shot / resulting action / transformed environment..."
                    rows={2}
                    required
                    className="w-full px-3.5 py-2.5 bg-[#090b14] border border-[#232943] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500"
                  />
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Nano Banana multi-turn generation ensures identical characters and environment between both frames.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Mode 3: Image Editor */}
          {studioMode === "edit" && (
            <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-4">
              <div className="flex items-center gap-2">
                <Wand2 className="w-4 h-4 text-cyan-400" />
                <h4 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                  Conversational Image Editing
                </h4>
              </div>

              {/* Source image picker */}
              <div>
                <label className="text-xs text-zinc-300 font-medium block mb-1">Source Image to Edit</label>
                {editSourcePreview ? (
                  <div className="relative aspect-video rounded-xl overflow-hidden border border-cyan-500/40 max-h-48">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={editSourcePreview} alt="Source" className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={() => {
                        setEditSourcePath("");
                        setEditSourcePreview("");
                      }}
                      className="absolute top-2 right-2 p-1.5 rounded-full bg-black/80 text-white hover:bg-red-600 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center p-6 rounded-xl border border-dashed border-[#2b3352] hover:border-cyan-500/60 bg-[#0c0e18] cursor-pointer text-center">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUpload(f, "editSrc");
                      }}
                    />
                    {uploadingEditSrc ? (
                      <span className="text-xs text-cyan-400 animate-pulse">Uploading source image...</span>
                    ) : (
                      <>
                        <Upload className="w-6 h-6 text-zinc-400 mb-1.5" />
                        <span className="text-xs font-medium text-zinc-200">Upload Image to Edit</span>
                        <span className="text-[10px] text-zinc-500 mt-0.5">Or enter local path below</span>
                      </>
                    )}
                  </label>
                )}
                {!editSourcePreview && (
                  <input
                    type="text"
                    value={editSourcePath}
                    onChange={(e) => setEditSourcePath(e.target.value)}
                    placeholder="Enter file path (e.g. outputs/image.png)"
                    className="w-full mt-2 px-3 py-1.5 bg-[#090b14] border border-[#21273f] rounded-lg text-xs text-zinc-200 focus:outline-none focus:border-cyan-500"
                  />
                )}
              </div>

              <div>
                <label className="text-xs text-zinc-300 font-medium block mb-1">Edit Instructions</label>
                <textarea
                  value={editPrompt}
                  onChange={(e) => setEditPrompt(e.target.value)}
                  placeholder="e.g. Change the jacket color to glowing neon cyan, add rain reflections on the ground, remove the background cars..."
                  rows={3}
                  required
                  className="w-full px-3.5 py-2.5 bg-[#090b14] border border-[#232943] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>
          )}

          {/* Model Selector */}
          <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
            <label className="text-xs font-semibold text-zinc-200 uppercase tracking-wider block">
              Gemini Image Model
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.values(IMAGE_MODELS).map((m) => {
                const isSelected = model === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleModelSelect(m.id)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "bg-cyan-600/15 border-cyan-500 text-white shadow-md shadow-cyan-500/10"
                        : "bg-[#090b14] border-[#21273f] text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-zinc-100">{m.name}</span>
                      {isSelected && <Check className="w-4 h-4 text-cyan-400" />}
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-2">{m.notes}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Aspect Ratio Selector (Matrix) */}
          <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
            <label className="text-xs font-semibold text-zinc-200 uppercase tracking-wider block">
              Aspect Ratio ({aspectRatio})
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {ASPECT_RATIOS.filter((ar) => currentModelSpec.supportedAspectRatios.includes(ar.value)).map((ar) => {
                const isSelected = aspectRatio === ar.value;
                return (
                  <button
                    key={ar.value}
                    type="button"
                    onClick={() => setAspectRatio(ar.value)}
                    className={`py-2 px-2.5 rounded-xl border text-xs font-medium text-center transition-all ${
                      isSelected
                        ? "bg-cyan-600/20 border-cyan-500 text-white shadow-sm"
                        : "bg-[#090b14] border-[#21273f] text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
                    }`}
                  >
                    <div className="font-semibold text-[11px]">{ar.value}</div>
                    <div className="text-[9px] text-zinc-500 truncate">{ar.label.split(" ")[1] || ""}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Size & Google Search Grounding */}
          <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                Output Quality & Grounding
              </h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Image Resolution / Size</label>
                <div className="grid grid-cols-3 gap-2">
                  {currentModelSpec.supportedSizes.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setImageSize(s)}
                      className={`px-3 py-2 rounded-xl text-xs font-semibold border text-center transition-all ${
                        imageSize === s
                          ? "bg-cyan-600/20 border-cyan-500 text-white"
                          : "bg-[#090b14] border-[#21273f] text-zinc-400 hover:text-zinc-200"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-zinc-400 block mb-1">Google Search Grounding</label>
                <label
                  className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl border transition-all ${
                    !currentModelSpec.supportsGoogleSearch
                      ? "opacity-40 cursor-not-allowed bg-[#090b14] border-[#21273f]"
                      : enableGoogleSearch
                      ? "bg-cyan-600/20 border-cyan-500 text-white cursor-pointer"
                      : "bg-[#090b14] border-[#21273f] text-zinc-400 cursor-pointer"
                  }`}
                >
                  <input
                    type="checkbox"
                    disabled={!currentModelSpec.supportsGoogleSearch}
                    checked={enableGoogleSearch && currentModelSpec.supportsGoogleSearch}
                    onChange={(e) => setEnableGoogleSearch(e.target.checked)}
                    className="w-4 h-4 rounded text-cyan-500"
                  />
                  <div className="text-xs">
                    <span className="font-semibold flex items-center gap-1">
                      <Search className="w-3.5 h-3.5 text-cyan-400" /> Web Grounding
                    </span>
                    <span className="text-[10px] text-zinc-500 block">
                      {currentModelSpec.supportsGoogleSearch ? "Factual accuracy & live data" : "Not supported on this model"}
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Save as Preference toggle */}
            <label className="flex items-center gap-2.5 pt-2 cursor-pointer">
              <input
                type="checkbox"
                checked={saveAsPreference}
                onChange={(e) => setSaveAsPreference(e.target.checked)}
                className="w-4 h-4 rounded bg-[#090b14] border-[#21273f] text-cyan-600"
              />
              <span className="text-xs text-zinc-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-zinc-400" />
                Save these image parameters as my permanent default preferences
              </span>
            </label>
          </div>

          {/* Reference Images (Generate & Keyframe modes) */}
          {studioMode !== "edit" && currentModelSpec.maxReferenceImages > 0 && (
            <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                  Character & Style References
                </h4>
                <span className="text-xs text-zinc-500">
                  {characterPaths.length + referencePaths.length} / {currentModelSpec.maxReferenceImages} total
                </span>
              </div>

              <div className="flex flex-wrap gap-2.5">
                {/* Character paths */}
                {characterPaths.map((p, i) => (
                  <div
                    key={`char-${i}`}
                    className="relative w-16 h-16 rounded-xl overflow-hidden border border-cyan-500/50 bg-[#090b14]"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={
                        p.includes("outputs")
                          ? `/api/media/${p.split("outputs")[1].replace(/^[/\\]+/, "").replace(/\\/g, "/")}`
                          : p
                      }
                      alt="Char"
                      className="w-full h-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const copy = [...characterPaths];
                        copy.splice(i, 1);
                        setCharacterPaths(copy);
                      }}
                      className="absolute top-1 right-1 p-0.5 rounded-full bg-black/80 text-white"
                    >
                      <X className="w-2.5 h-2.5" />
                    </button>
                    <span className="absolute bottom-0 inset-x-0 bg-black/70 text-[8px] text-center text-cyan-300 py-0.5">
                      Character
                    </span>
                  </div>
                ))}

                {/* Upload button for character */}
                {characterPaths.length < currentModelSpec.maxCharacterReferences && (
                  <label className="w-16 h-16 rounded-xl border border-dashed border-[#2b3352] hover:border-cyan-500/60 bg-[#090b14] flex flex-col items-center justify-center cursor-pointer text-center group">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUpload(f, "char");
                      }}
                    />
                    <Plus className="w-4 h-4 text-zinc-400 group-hover:text-cyan-400" />
                    <span className="text-[9px] text-zinc-400 mt-0.5">Character</span>
                  </label>
                )}

                {/* General references */}
                {referencePaths.map((p, i) => (
                  <div
                    key={`ref-${i}`}
                    className="relative w-16 h-16 rounded-xl overflow-hidden border border-violet-500/50 bg-[#090b14]"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={
                        p.includes("outputs")
                          ? `/api/media/${p.split("outputs")[1].replace(/^[/\\]+/, "").replace(/\\/g, "/")}`
                          : p
                      }
                      alt="Ref"
                      className="w-full h-full object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const copy = [...referencePaths];
                        copy.splice(i, 1);
                        setReferencePaths(copy);
                      }}
                      className="absolute top-1 right-1 p-0.5 rounded-full bg-black/80 text-white"
                    >
                      <X className="w-2.5 h-2.5" />
                    </button>
                    <span className="absolute bottom-0 inset-x-0 bg-black/70 text-[8px] text-center text-violet-300 py-0.5">
                      Style
                    </span>
                  </div>
                ))}

                {/* Upload button for reference */}
                {characterPaths.length + referencePaths.length < currentModelSpec.maxReferenceImages && (
                  <label className="w-16 h-16 rounded-xl border border-dashed border-[#2b3352] hover:border-violet-500/60 bg-[#090b14] flex flex-col items-center justify-center cursor-pointer text-center group">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUpload(f, "ref");
                      }}
                    />
                    <Plus className="w-4 h-4 text-zinc-400 group-hover:text-violet-400" />
                    <span className="text-[9px] text-zinc-400 mt-0.5">Style Ref</span>
                  </label>
                )}
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorBanner && (
            <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-red-300">Image Generation Notice</div>
                <pre className="whitespace-pre-wrap font-mono text-[11px] max-h-40 overflow-y-auto">
                  {errorBanner}
                </pre>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 px-6 rounded-xl font-semibold text-sm bg-gradient-to-r from-cyan-600 via-teal-600 to-indigo-600 hover:from-cyan-500 hover:via-teal-500 hover:to-indigo-500 text-white shadow-xl shadow-cyan-600/25 flex items-center justify-center gap-2.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Generating Image with Nano Banana...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 fill-white" />
                <span>
                  {studioMode === "generate"
                    ? "Generate High-Res Image"
                    : studioMode === "keyframes"
                    ? `Generate ${numKeyframes} Keyframe${numKeyframes > 1 ? "s" : ""}`
                    : "Apply Image Edit"}
                </span>
              </>
            )}
          </button>
        </form>

        {/* Right Column: Results Gallery & Lightbox + Recent Media Panel (5 columns) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Quick-Access Recent Processed Media Panel */}
          <RecentProcessedPanel
            currentModel={model}
            supportsKeyframes={false}
            supportsCharacters={currentModelSpec.maxCharacterReferences > 0}
            maxCharacterCount={currentModelSpec.maxCharacterReferences}
            currentCharacterCount={characterPaths.length}
            onAddCharacter={(filePath) => {
              if (
                characterPaths.length < currentModelSpec.maxCharacterReferences &&
                !characterPaths.includes(filePath)
              ) {
                setCharacterPaths([...characterPaths, filePath]);
              }
            }}
            onUseAsEditSource={(filePath, previewUrl) => {
              setStudioMode("edit");
              setEditSourcePath(filePath);
              setEditSourcePreview(previewUrl);
            }}
          />

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">
              Current Session Renders ({resultImages.length})
            </h3>

            {resultImages.length === 0 ? (
              <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-6 text-center space-y-2">
                <div className="w-10 h-10 rounded-xl bg-[#171a2e] flex items-center justify-center mx-auto text-cyan-400 border border-[#272e48]">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-semibold text-zinc-200">Session Images</h4>
                <p className="text-[11px] text-zinc-400 max-w-xs mx-auto">
                  Images generated in this browser session will also appear here in full resolution.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {resultImages.map((img, idx) => (
                  <div
                    key={idx}
                    className="bg-[#121524] border border-[#21273f] rounded-2xl p-4 space-y-3 shadow-xl"
                  >
                    <div className="relative rounded-xl overflow-hidden border border-[#262e4a] bg-black aspect-video group">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={img.url} alt="Generated" className="w-full h-full object-contain" />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                        <button
                          onClick={() => setPreviewModalImg(img)}
                          className="p-2 rounded-xl bg-white/20 hover:bg-white/30 text-white backdrop-blur-sm transition-colors"
                          title="Open Fullscreen"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <a
                          href={img.url}
                          download
                          className="p-2 rounded-xl bg-white/20 hover:bg-white/30 text-white backdrop-blur-sm transition-colors"
                          title="Download PNG"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      </div>
                    </div>

                    <p className="text-xs text-zinc-300 italic line-clamp-2 bg-[#090b14] p-2 rounded-lg border border-[#1b2034]">
                      &quot;{img.prompt}&quot;
                    </p>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[11px] font-mono text-zinc-500 truncate max-w-[150px]">
                        {img.path.split(/[\\/]/).pop()}
                      </span>
                      <button
                        onClick={() => {
                          // Route to video studio with this keyframe
                          router.push(`/video?keyframe=${encodeURIComponent(img.path)}`);
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-violet-600/20 text-violet-300 hover:bg-violet-600/30 border border-violet-500/30 transition-colors"
                      >
                        <span>Use as Keyframe</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Lightbox / Zoom Modal */}
      {previewModalImg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
          <div className="max-w-4xl w-full bg-[#111320] border border-[#262c47] rounded-2xl overflow-hidden flex flex-col shadow-2xl">
            <div className="p-4 border-b border-[#21263d] flex items-center justify-between">
              <span className="text-sm font-semibold text-zinc-200 truncate max-w-md">
                {previewModalImg.prompt}
              </span>
              <button
                onClick={() => setPreviewModalImg(null)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 bg-black flex items-center justify-center max-h-[75vh]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewModalImg.url}
                alt="Full preview"
                className="max-h-[70vh] w-auto object-contain rounded-lg shadow-lg"
              />
            </div>
            <div className="p-4 border-t border-[#21263d] bg-[#141829] flex items-center justify-between">
              <span className="text-xs font-mono text-zinc-400 truncate max-w-sm">
                {previewModalImg.path}
              </span>
              <div className="flex items-center gap-3">
                <a
                  href={previewModalImg.url}
                  download
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white transition-colors"
                >
                  <Download className="w-4 h-4" /> Download PNG
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

