"use client";

import { useState, useEffect } from "react";
import {
  Settings,
  CheckCircle2,
  RotateCcw,
  Save,
  Activity,
  HardDrive,
  Video,
  Image as ImageIcon,
  KeyRound,
  Layers,
  HelpCircle,
  Sparkles,
  Eye,
  EyeOff,
  Globe,
  Key,
} from "lucide-react";
import { VIDEO_MODELS, IMAGE_MODELS, ASPECT_RATIOS } from "@/lib/constants";

export function SettingsManager() {
  // API Key & Port .env State
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [currentMaskedKey, setCurrentMaskedKey] = useState("");
  const [portInput, setPortInput] = useState("8989");
  const [isApiKeySaving, setIsApiKeySaving] = useState(false);
  const [apiKeyMsg, setApiKeyMsg] = useState<{ text: string; success: boolean } | null>(null);

  // Video Preferences
  const [videoModel, setVideoModel] = useState("gemini-omni-1.1-flash");
  const [videoAspect, setVideoAspect] = useState("16:9");
  const [videoResolution, setVideoResolution] = useState("standard");
  const [videoDuration, setVideoDuration] = useState(8);

  // Image Preferences
  const [imageModel, setImageModel] = useState("gemini-nano-banana-2.1");
  const [imageAspect, setImageAspect] = useState("16:9");
  const [imageSize, setImageSize] = useState("2K");
  const [imageSearch, setImageSearch] = useState(false);

  // Storage
  const [outputDir, setOutputDir] = useState("");

  // Diagnostics & Status
  const [healthStatus, setHealthStatus] = useState<string>("");
  const [healthLoading, setHealthLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Load existing preferences
  const loadPreferences = async () => {
    try {
      const res = await fetch("/api/mcp/preferences");
      if (res.ok) {
        const data = await res.json();
        const prefs = data.preferences || {};
        if (prefs.video) {
          if (prefs.video.model) setVideoModel(prefs.video.model);
          if (prefs.video.aspect_ratio) setVideoAspect(prefs.video.aspect_ratio);
          if (prefs.video.resolution) setVideoResolution(prefs.video.resolution);
          if (prefs.video.duration_seconds) setVideoDuration(prefs.video.duration_seconds);
        }
        if (prefs.image) {
          if (prefs.image.model) setImageModel(prefs.image.model);
          if (prefs.image.aspect_ratio) setImageAspect(prefs.image.aspect_ratio);
          if (prefs.image.image_size) setImageSize(prefs.image.image_size);
          if (prefs.image.enable_google_search !== undefined) setImageSearch(prefs.image.enable_google_search);
        }
        if (prefs.output_dir) {
          setOutputDir(prefs.output_dir);
        }
      }
    } catch (e) {
      console.error("Failed to load preferences:", e);
    }
  };

  const runHealthCheck = async () => {
    setHealthLoading(true);
    try {
      const res = await fetch("/api/mcp/tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool: "check_api_status", args: {} }),
      });
      const data = await res.json();
      setHealthStatus(data.content || "Health check failed");
    } catch (e: any) {
      setHealthStatus(`Error checking health: ${e?.message}`);
    } finally {
      setHealthLoading(false);
    }
  };

  const fetchEnvConfig = async () => {
    try {
      const res = await fetch("/api/env");
      if (res.ok) {
        const data = await res.json();
        if (data.masked_key) setCurrentMaskedKey(data.masked_key);
        if (data.port) setPortInput(String(data.port));
      }
    } catch (e) {
      console.error("Failed to fetch env config:", e);
    }
  };

  const handleSaveApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim() && !portInput.trim()) return;

    setIsApiKeySaving(true);
    setApiKeyMsg(null);

    try {
      const res = await fetch("/api/env", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          gemini_api_key: apiKeyInput.trim() || undefined,
          port: portInput ? Number(portInput) : undefined,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setApiKeyMsg({
          text: ".env file updated successfully! New API key is now active.",
          success: true,
        });
        setApiKeyInput("");
        await fetchEnvConfig();
        await runHealthCheck();
      } else {
        setApiKeyMsg({
          text: data.error || "Failed to update .env",
          success: false,
        });
      }
    } catch (err: any) {
      setApiKeyMsg({
        text: err?.message || "Error updating .env",
        success: false,
      });
    } finally {
      setIsApiKeySaving(false);
      setTimeout(() => setApiKeyMsg(null), 5000);
    }
  };

  useEffect(() => {
    loadPreferences();
    fetchEnvConfig();
    runHealthCheck();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveStatus(null);

    try {
      // 1. Save Video Preferences
      await fetch("/api/mcp/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          media_type: "video",
          model: videoModel,
          aspect_ratio: videoAspect,
          resolution: videoResolution,
          duration_seconds: videoDuration,
        }),
      });

      // 2. Save Image Preferences
      await fetch("/api/mcp/preferences", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          media_type: "image",
          model: imageModel,
          aspect_ratio: imageAspect,
          image_size: imageSize,
          enable_google_search: imageSearch,
        }),
      });

      // 3. Save Output Directory if specified
      if (outputDir.trim()) {
        await fetch("/api/mcp/preferences", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            output_dir: outputDir.trim(),
          }),
        });
      }

      setSaveStatus("Preferences successfully updated and saved to user_preferences.json!");
      setTimeout(() => setSaveStatus(null), 4000);
    } catch (err: any) {
      setSaveStatus(`Failed to save preferences: ${err?.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("Are you sure you want to reset all preferences to defaults?")) return;
    setIsSaving(true);
    try {
      const res = await fetch("/api/mcp/preferences", { method: "DELETE" });
      if (res.ok) {
        await loadPreferences();
        setSaveStatus("Preferences reset to default values.");
        setTimeout(() => setSaveStatus(null), 4000);
      }
    } catch (e: any) {
      setSaveStatus(`Reset failed: ${e?.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1f2438] pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Settings className="w-8 h-8 text-indigo-400" />
            <span>Preferences & System Settings</span>
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Configure default generative models, aspect ratios, storage folders, and run pre-flight diagnostics.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            type="button"
            onClick={handleReset}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#121524] hover:bg-red-950/40 text-red-400 hover:text-red-300 border border-[#21273f] hover:border-red-800/50 transition-colors disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
        </div>
      </div>

      {saveStatus && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded-xl text-xs text-emerald-200 flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{saveStatus}</span>
        </div>
      )}

      {/* API Key & Port .env Configuration Card */}
      <div className="bg-[#121524] border border-violet-500/40 rounded-2xl p-6 space-y-4 shadow-xl shadow-violet-500/5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1b2034] pb-3">
          <div className="flex items-center gap-2.5">
            <Key className="w-5 h-5 text-violet-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">Gemini API Key & Port (.env Configuration)</h3>
              <p className="text-xs text-zinc-400">
                Directly view, update, and overwrite the API Key and web server port in your local .env file
              </p>
            </div>
          </div>
          {currentMaskedKey && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded-lg">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Active: {currentMaskedKey}</span>
            </div>
          )}
        </div>

        {apiKeyMsg && (
          <div
            className={`p-3.5 rounded-xl text-xs flex items-center gap-2 animate-in fade-in ${
              apiKeyMsg.success
                ? "bg-emerald-950/40 border border-emerald-800/60 text-emerald-200"
                : "bg-red-950/40 border border-red-800/60 text-red-200"
            }`}
          >
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{apiKeyMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleSaveApiKey} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            {/* API Key Input */}
            <div className="md:col-span-9 space-y-1">
              <label className="text-xs font-medium text-zinc-300 block">
                Update GEMINI_API_KEY (Google AI Studio Key)
              </label>
              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="Paste new Gemini API Key (starts with AIzaSy... or AQ...)"
                  className="w-full pl-3.5 pr-10 py-2.5 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-violet-500 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-200"
                >
                  {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Port Input */}
            <div className="md:col-span-3 space-y-1">
              <label className="text-xs font-medium text-zinc-300 flex items-center gap-1">
                <Globe className="w-3.5 h-3.5 text-cyan-400" /> Web Port
              </label>
              <input
                type="number"
                value={portInput}
                onChange={(e) => setPortInput(e.target.value)}
                placeholder="8989"
                className="w-full px-3.5 py-2.5 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isApiKeySaving || (!apiKeyInput.trim() && !portInput.trim())}
              className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white shadow transition-all disabled:opacity-50 cursor-pointer"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{isApiKeySaving ? "Updating .env..." : "Overwrite .env & Apply Key"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Main Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Default Video Preferences */}
        <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-6 space-y-5">
          <div className="flex items-center gap-2.5 border-b border-[#1b2034] pb-3">
            <Video className="w-5 h-5 text-violet-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">Default Video Preferences</h3>
              <p className="text-xs text-zinc-400">Pre-selected values for new video generation sessions</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {/* Model */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Model</label>
              <select
                value={videoModel}
                onChange={(e) => setVideoModel(e.target.value)}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
              >
                {Object.values(VIDEO_MODELS).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Aspect Ratio */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Aspect Ratio</label>
              <select
                value={videoAspect}
                onChange={(e) => setVideoAspect(e.target.value)}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
              >
                <option value="16:9">16:9 (Landscape)</option>
                <option value="9:16">9:16 (Portrait / Reel)</option>
              </select>
            </div>

            {/* Resolution */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Resolution</label>
              <select
                value={videoResolution}
                onChange={(e) => setVideoResolution(e.target.value)}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
              >
                <option value="standard">standard (Omni)</option>
                <option value="720p">720p (Fast HD)</option>
                <option value="1080p">1080p (Full HD)</option>
                <option value="4k">4k (Ultra HD)</option>
              </select>
            </div>

            {/* Duration */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Duration</label>
              <select
                value={videoDuration}
                onChange={(e) => setVideoDuration(Number(e.target.value))}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-violet-500"
              >
                <option value={5}>5 Seconds</option>
                <option value={8}>8 Seconds (Veo standard)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 2: Default Image Preferences */}
        <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-6 space-y-5">
          <div className="flex items-center gap-2.5 border-b border-[#1b2034] pb-3">
            <ImageIcon className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">Default Image Preferences</h3>
              <p className="text-xs text-zinc-400">Pre-selected values for Gemini Nano Banana image generation</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {/* Model */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Model</label>
              <select
                value={imageModel}
                onChange={(e) => setImageModel(e.target.value)}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500"
              >
                {Object.values(IMAGE_MODELS).map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Aspect Ratio */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Aspect Ratio</label>
              <select
                value={imageAspect}
                onChange={(e) => setImageAspect(e.target.value)}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500"
              >
                {ASPECT_RATIOS.map((ar) => (
                  <option key={ar.value} value={ar.value}>
                    {ar.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Image Size */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Resolution Size</label>
              <select
                value={imageSize}
                onChange={(e) => setImageSize(e.target.value)}
                className="w-full px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="512px">512px (Fast Draft)</option>
                <option value="1K">1K (Standard)</option>
                <option value="2K">2K (High-Res 1440p)</option>
                <option value="4K">4K (Ultra-Res)</option>
              </select>
            </div>

            {/* Google Search Grounding */}
            <div>
              <label className="text-xs font-medium text-zinc-300 block mb-1.5">Default Search Grounding</label>
              <label className="flex items-center gap-2 px-3 py-2 bg-[#090b14] border border-[#21273f] rounded-xl cursor-pointer">
                <input
                  type="checkbox"
                  checked={imageSearch}
                  onChange={(e) => setImageSearch(e.target.checked)}
                  className="w-4 h-4 rounded text-cyan-600"
                />
                <span className="text-xs text-zinc-200">Enable Google Grounding</span>
              </label>
            </div>
          </div>
        </div>

        {/* Section 3: Storage Folder Configuration */}
        <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2.5 border-b border-[#1b2034] pb-3">
            <HardDrive className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">Media Storage Destination</h3>
              <p className="text-xs text-zinc-400">Directory path where generated videos and images are saved</p>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-zinc-300 block mb-1.5">
              Custom Output Directory (Leave empty or &apos;default&apos; for workspace outputs/ folder)
            </label>
            <input
              type="text"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
              placeholder="e.g. D:\Renders\GeminiMedia or outputs/"
              className="w-full px-3.5 py-2.5 bg-[#090b14] border border-[#21273f] rounded-xl text-xs text-zinc-100 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        {/* Save Button */}
        <button
          type="submit"
          disabled={isSaving}
          className="w-full py-3 px-6 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-xl shadow-indigo-600/25 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>Save All Preferences</span>
        </button>
      </form>

      {/* Section 4: Pre-flight Diagnostic Health Check */}
      <div className="bg-[#121524] border border-[#21273f] rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-[#1b2034] pb-3">
          <div className="flex items-center gap-2.5">
            <Activity className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">MCP Pre-flight Diagnostics</h3>
              <p className="text-xs text-zinc-400">Verifies API key formatting, GenAI client readiness, and output storage</p>
            </div>
          </div>

          <button
            onClick={runHealthCheck}
            disabled={healthLoading}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#1a1e30] hover:bg-[#252b44] text-zinc-200 border border-[#262c47] transition-colors disabled:opacity-50"
          >
            {healthLoading ? "Checking..." : "Re-run Diagnostic"}
          </button>
        </div>

        <pre className="p-4 bg-[#090b14] border border-[#1f253d] rounded-xl font-mono text-xs text-zinc-300 whitespace-pre-wrap max-h-60 overflow-y-auto">
          {healthStatus || "Loading diagnostics..."}
        </pre>
      </div>
    </div>
  );
}

