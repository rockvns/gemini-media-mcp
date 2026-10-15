"use client";

import { useState, useEffect } from "react";
import { Sparkles, Wand2, Play, Video, Film, Sliders, Check, AlertCircle, Bookmark } from "lucide-react";
import { VIDEO_MODELS } from "@/lib/constants";
import { DirectorModal } from "./DirectorModal";
import { KeyframeUploader, KeyframeMode } from "./KeyframeUploader";
import { CharacterRefPicker } from "./CharacterRefPicker";
import { ActiveOperationCard, OperationData } from "./ActiveOperationCard";
import { RecentProcessedPanel } from "@/components/gallery/RecentProcessedPanel";

export function VideoGenerator() {
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [model, setModel] = useState("gemini-omni-1.1-flash");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [resolution, setResolution] = useState("standard");
  const [durationSeconds, setDurationSeconds] = useState(8);
  const [saveAsPreference, setSaveAsPreference] = useState(false);

  // Keyframes
  const [keyframeMode, setKeyframeMode] = useState<KeyframeMode>("none");
  const [firstFramePath, setFirstFramePath] = useState("");
  const [firstFramePreview, setFirstFramePreview] = useState("");
  const [lastFramePath, setLastFramePath] = useState("");
  const [lastFramePreview, setLastFramePreview] = useState("");

  // Characters
  const [characterPaths, setCharacterPaths] = useState<string[]>([]);

  // Modals & UI States
  const [directorOpen, setDirectorOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<OperationData | null>(null);

  // Load saved preferences on mount
  useEffect(() => {
    fetch("/api/mcp/preferences")
      .then((r) => r.json())
      .then((data) => {
        if (data.preferences?.video) {
          const v = data.preferences.video;
          if (v.model) setModel(v.model);
          if (v.aspect_ratio) setAspectRatio(v.aspect_ratio);
          if (v.resolution) setResolution(v.resolution);
          if (v.duration_seconds) setDurationSeconds(v.duration_seconds);
        }
      })
      .catch(() => {});
  }, []);

  const currentModelSpec = VIDEO_MODELS[model] || VIDEO_MODELS["veo-3.1-generate-preview"];

  // Handle Model change: adjust resolution/duration if unsupported
  const handleModelSelect = (newModel: string) => {
    setModel(newModel);
    const spec = VIDEO_MODELS[newModel];
    if (spec) {
      if (!spec.supportedResolutions.includes(resolution)) {
        setResolution(spec.supportedResolutions[0]);
      }
      if (!spec.supportedAspectRatios.includes(aspectRatio)) {
        setAspectRatio(spec.supportedAspectRatios[0]);
      }
      if (!spec.supportedDurations.includes(durationSeconds)) {
        setDurationSeconds(spec.defaultDuration);
      }
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsSubmitting(true);
    setErrorBanner(null);

    try {
      const payload: Record<string, any> = {
        prompt: prompt.trim(),
        model,
        aspect_ratio: aspectRatio,
        resolution,
        duration_seconds: durationSeconds,
        save_as_preference: saveAsPreference,
        wait_for_completion: false, // Zero-timeout non-blocking async dispatch!
      };

      if (negativePrompt.trim()) {
        payload.negative_prompt = negativePrompt.trim();
      }

      if (keyframeMode === "single" && firstFramePath) {
        payload.first_frame_path = firstFramePath;
      } else if (keyframeMode === "pair") {
        if (firstFramePath) payload.first_frame_path = firstFramePath;
        if (lastFramePath) payload.last_frame_path = lastFramePath;
      }

      if (characterPaths.length > 0) {
        payload.character_paths = characterPaths;
      }

      const res = await fetch("/api/mcp/tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool: "generate_video",
          args: payload,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setErrorBanner(data.content || data.error || "Failed to dispatch video generation");
        setIsSubmitting(false);
        return;
      }

      // Extract operation_name from tool response if string contains 'Operation ID: xyz'
      const text = data.content || "";
      const match = text.match(/Operation ID:\s*([^\s\n\r]+)/i) || text.match(/operations\/([^\s\n\r]+)/);
      const opId = match ? (match[1].startsWith("operations/") ? match[1] : match[0].split(":")[1].trim()) : null;

      if (opId) {
        const newOp: OperationData = {
          operation_name: opId,
          model,
          prompt,
          status: "IN_PROGRESS",
          created_at: new Date().toISOString(),
        };
        setActiveJob(newOp);
      } else {
        // Omni or direct return
        setErrorBanner(text);
      }
    } catch (err: any) {
      setErrorBanner(err?.message || "Generation error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1f2438] pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Video className="w-8 h-8 text-violet-400" />
            <span>Video Generation Studio</span>
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Google Veo 3.1 & Gemini Omni with native audio, multi-keyframe interpolation, and character anchors.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setDirectorOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-[#161a2b] border border-violet-500/30 text-violet-300 hover:bg-violet-600/20 hover:border-violet-500/50 shadow transition-all self-start md:self-auto"
        >
          <Wand2 className="w-4 h-4 text-violet-400" />
          <span>Director Assistant</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form: 7 or 8 columns */}
        <form onSubmit={handleGenerate} className="lg:col-span-7 space-y-6">
          {/* Prompt Section */}
          <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-violet-400" /> Scene & Motion Description
              </label>
              <span className="text-xs text-zinc-500">{prompt.length} chars</span>
            </div>

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the cinematic action, camera movement, environmental lighting, and audio soundscape..."
              rows={4}
              required
              className="w-full px-4 py-3 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
            />

            <div>
              <label className="text-xs font-medium text-zinc-400 mb-1 block">
                Negative Prompt (Optional elements to avoid)
              </label>
              <input
                type="text"
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="blurry, distorted, oversaturated, text artifacts..."
                className="w-full px-3.5 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-violet-500"
              />
            </div>
          </div>

          {/* Model Selection */}
          <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-zinc-200 uppercase tracking-wider flex items-center gap-2">
                <Film className="w-4 h-4 text-cyan-400" /> Video Model
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.values(VIDEO_MODELS).map((m) => {
                const isSelected = model === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => handleModelSelect(m.id)}
                    className={`p-3.5 rounded-xl border text-left transition-all relative ${
                      isSelected
                        ? "bg-violet-600/15 border-violet-500 text-white shadow-md shadow-violet-500/10"
                        : "bg-[#090b14] border-[#21273f] text-zinc-400 hover:border-zinc-700 hover:text-zinc-200"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs text-zinc-100">{m.name}</span>
                      {isSelected && <Check className="w-4 h-4 text-violet-400" />}
                    </div>
                    <p className="text-[11px] text-zinc-400 line-clamp-2">{m.notes}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Keyframes (Only on models that support keyframes, e.g. Veo 3.1) */}
          {currentModelSpec.supportsKeyframes && (
            <KeyframeUploader
              mode={keyframeMode}
              onModeChange={setKeyframeMode}
              firstFramePath={firstFramePath}
              onFirstFrameChange={(p, prev) => {
                setFirstFramePath(p);
                setFirstFramePreview(prev || "");
              }}
              lastFramePath={lastFramePath}
              onLastFrameChange={(p, prev) => {
                setLastFramePath(p);
                setLastFramePreview(prev || "");
              }}
              firstFramePreview={firstFramePreview}
              lastFramePreview={lastFramePreview}
            />
          )}

          {/* Character References (Veo 3.1 & Omni) */}
          {currentModelSpec.maxReferenceImages > 0 && (
            <CharacterRefPicker
              paths={characterPaths}
              onChange={setCharacterPaths}
              maxCount={currentModelSpec.maxReferenceImages}
            />
          )}

          {/* Generation Settings: Aspect Ratio, Resolution, Duration */}
          <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                Cinematography Parameters
              </h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Aspect Ratio */}
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Aspect Ratio</label>
                <div className="grid grid-cols-2 gap-2">
                  {currentModelSpec.supportedAspectRatios.map((ar) => (
                    <button
                      key={ar}
                      type="button"
                      onClick={() => setAspectRatio(ar)}
                      className={`px-3 py-2 rounded-xl text-xs font-medium border text-center transition-all ${
                        aspectRatio === ar
                          ? "bg-violet-600/20 border-violet-500 text-white"
                          : "bg-[#090b14] border-[#21273f] text-zinc-400 hover:text-zinc-200"
                      }`}
                    >
                      {ar} {ar === "16:9" ? "(Wide)" : "(Reel)"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Resolution */}
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Resolution</label>
                <select
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
                >
                  {currentModelSpec.supportedResolutions.map((r) => (
                    <option key={r} value={r}>
                      {r.toUpperCase()} {r === "4k" ? "(High Latency)" : ""}
                    </option>
                  ))}
                </select>
              </div>

              {/* Duration */}
              <div>
                <label className="text-xs text-zinc-400 block mb-1">Duration</label>
                <select
                  value={durationSeconds}
                  onChange={(e) => setDurationSeconds(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
                >
                  {currentModelSpec.supportedDurations.map((d) => (
                    <option key={d} value={d}>
                      {d} Seconds
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Save as Preference toggle */}
            <label className="flex items-center gap-2.5 pt-2 cursor-pointer">
              <input
                type="checkbox"
                checked={saveAsPreference}
                onChange={(e) => setSaveAsPreference(e.target.checked)}
                className="w-4 h-4 rounded bg-[#090b14] border-[#21273f] text-violet-600 focus:ring-violet-500"
              />
              <span className="text-xs text-zinc-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-zinc-400" />
                Save these video parameters as my permanent default preferences
              </span>
            </label>
          </div>

          {/* Error Banner */}
          {errorBanner && (
            <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-red-300">Generation Notice</div>
                <pre className="whitespace-pre-wrap font-mono text-[11px] max-h-40 overflow-y-auto">
                  {errorBanner}
                </pre>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || !prompt.trim()}
            className="w-full py-3.5 px-6 rounded-xl font-semibold text-sm bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 hover:from-violet-500 hover:via-indigo-500 hover:to-cyan-400 text-white shadow-xl shadow-violet-600/25 flex items-center justify-center gap-2.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Dispatching to Google Veo...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Generate Video with {currentModelSpec.name.split(" ")[0]}</span>
              </>
            )}
          </button>
        </form>

        {/* Right Column: Active Job Card / Monitor & Recent Processed Media (5 columns) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">
              Active Video Render
            </h3>

            {activeJob ? (
              <ActiveOperationCard
                operation={activeJob}
                onUpdated={(updated) => setActiveJob(updated)}
                autoPoll={true}
              />
            ) : (
              <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-6 text-center space-y-2">
                <div className="w-10 h-10 rounded-xl bg-[#171a2e] flex items-center justify-center mx-auto text-violet-400 border border-[#272e48]">
                  <Video className="w-5 h-5" />
                </div>
                <h4 className="text-xs font-semibold text-zinc-200">No Video In Progress</h4>
                <p className="text-[11px] text-zinc-400 max-w-xs mx-auto">
                  Configure your prompt and click generate. Veo renders dispatch asynchronously with zero timeout.
                </p>
              </div>
            )}
          </div>

          {/* Quick-Access Recent Processed Media Panel */}
          <RecentProcessedPanel
            currentModel={model}
            supportsKeyframes={currentModelSpec.supportsKeyframes}
            supportsCharacters={currentModelSpec.maxReferenceImages > 0}
            maxCharacterCount={currentModelSpec.maxReferenceImages}
            currentCharacterCount={characterPaths.length}
            onAddCharacter={(filePath) => {
              if (characterPaths.length < currentModelSpec.maxReferenceImages && !characterPaths.includes(filePath)) {
                setCharacterPaths([...characterPaths, filePath]);
              }
            }}
            onSetKeyframe={(frameType, filePath, previewUrl) => {
              if (currentModelSpec.supportsKeyframes) {
                if (frameType === "first") {
                  setKeyframeMode(keyframeMode === "none" ? "single" : keyframeMode);
                  setFirstFramePath(filePath);
                  setFirstFramePreview(previewUrl);
                } else {
                  setKeyframeMode("pair");
                  setLastFramePath(filePath);
                  setLastFramePreview(previewUrl);
                }
              }
            }}
          />
        </div>
      </div>

      {/* Director Assistant Modal */}
      <DirectorModal
        isOpen={directorOpen}
        onClose={() => setDirectorOpen(false)}
        onApplyPrompt={(p) => setPrompt(p)}
      />
    </div>
  );
}

