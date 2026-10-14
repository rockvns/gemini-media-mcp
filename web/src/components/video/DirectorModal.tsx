"use client";

import { useState } from "react";
import { Sparkles, X, Wand2, Film, Camera, Music } from "lucide-react";

interface DirectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyPrompt: (prompt: string) => void;
}

const MOODS = [
  "Cinematic & Photorealistic",
  "Cyberpunk Neon & Rainy",
  "Warm Golden Hour",
  "Dark Moody Noir",
  "Ethereal Dreamscape",
  "Sci-Fi Holographic",
  "Vintage 1970s 35mm Film Grain",
  "High-Octane Action",
];

const MOTIONS = [
  "Dynamic drone shot swooping over the scene",
  "FPV high-speed dive and orbit",
  "Smooth Steadicam tracking shot following subject",
  "Dolly zoom (vertigo effect) intensifying drama",
  "Cinematic slow-motion 120fps pan",
  "Handheld documentary style with natural micro-shakes",
  "Static locked-off telephoto shot with deep depth of field",
];

export function DirectorModal({ isOpen, onClose, onApplyPrompt }: DirectorModalProps) {
  const [concept, setConcept] = useState("");
  const [mood, setMood] = useState(MOODS[0]);
  const [cameraMotion, setCameraMotion] = useState(MOTIONS[0]);
  const [audioCue, setAudioCue] = useState("Immersive binaural audio, ambient wind, subtle orchestral score");
  const [lighting, setLighting] = useState("Volumetric lighting, soft rim light, natural reflections");

  if (!isOpen) return null;

  const handleGenerate = () => {
    if (!concept.trim()) return;

    const fullPrompt = [
      `[Cinematic Concept]: ${concept.trim()}`,
      `[Mood & Style]: ${mood}`,
      `[Camera Motion]: ${cameraMotion}`,
      `[Lighting & Atmosphere]: ${lighting}`,
      `[Native Audio & Sound]: ${audioCue}`,
    ].join(". ");

    onApplyPrompt(fullPrompt);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-[#111320] border border-[#262c47] rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#21263d] flex items-center justify-between bg-[#141829]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-violet-600/20 text-violet-400">
              <Film className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Veo Director Assistant</h3>
              <p className="text-xs text-zinc-400">Compose cinematic prompts with shot physics, lighting, and audio</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-[#1f243b] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
              Core Concept / Subject
            </label>
            <textarea
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
              placeholder="e.g. A futuristic samurai walking through a neon-lit Tokyo market at night..."
              rows={2}
              className="w-full px-3.5 py-2.5 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-violet-400" /> Desired Mood
              </label>
              <select
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                className="w-full px-3.5 py-2 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-violet-500"
              >
                {MOODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Camera className="w-3.5 h-3.5 text-cyan-400" /> Camera Motion
              </label>
              <select
                value={cameraMotion}
                onChange={(e) => setCameraMotion(e.target.value)}
                className="w-full px-3.5 py-2 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-violet-500"
              >
                {MOTIONS.map((mot) => (
                  <option key={mot} value={mot}>
                    {mot}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5">
              Lighting & Environmental Atmosphere
            </label>
            <input
              type="text"
              value={lighting}
              onChange={(e) => setLighting(e.target.value)}
              className="w-full px-3.5 py-2 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-violet-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Music className="w-3.5 h-3.5 text-emerald-400" /> Native Audio & Sound Design
            </label>
            <input
              type="text"
              value={audioCue}
              onChange={(e) => setAudioCue(e.target.value)}
              placeholder="e.g. Crisp footsteps, ambient market chatter, distant thunder..."
              className="w-full px-3.5 py-2 bg-[#090b14] border border-[#232943] rounded-xl text-sm text-zinc-100 focus:outline-none focus:border-violet-500"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[#21263d] bg-[#141829] flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-sm text-zinc-400 hover:text-white hover:bg-[#1e2338] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={!concept.trim()}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-violet-600/30 transition-all"
          >
            <Wand2 className="w-4 h-4" /> Apply to Director Prompt
          </button>
        </div>
      </div>
    </div>
  );
}

