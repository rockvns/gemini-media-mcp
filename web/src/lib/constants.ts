export interface VideoModelSpec {
  id: string;
  name: string;
  supportedResolutions: string[];
  supportedAspectRatios: string[];
  supportedDurations: number[];
  defaultDuration: number;
  maxReferenceImages: number;
  supportsKeyframes: boolean;
  nativeAudio: boolean;
  notes: string;
}

export interface ImageModelSpec {
  id: string;
  name: string;
  supportedSizes: string[];
  supportedAspectRatios: string[];
  supportsGoogleSearch: boolean;
  maxReferenceImages: number;
  maxCharacterReferences: number;
  notes: string;
}

export interface MediaAsset {
  filename: string;
  relativePath: string;
  absolutePath: string;
  url: string;
  type: "video" | "image";
  size: number;
  createdAt: string;
  model?: string;
  prompt?: string;
  aspectRatio?: string;
  resolution?: string;
}

export const VIDEO_MODELS: Record<string, VideoModelSpec> = {
  "gemini-omni-1.1-flash": {
    id: "gemini-omni-1.1-flash",
    name: "Gemini Omni 1.1 Flash (Recommended Video)",
    supportedResolutions: ["standard"],
    supportedAspectRatios: ["16:9"],
    supportedDurations: [5, 8],
    defaultDuration: 8,
    maxReferenceImages: 1,
    supportsKeyframes: false,
    nativeAudio: true,
    notes: "Ultra-fast multimodal video generation via Interactions API.",
  },
  "veo-3.1-generate-preview": {
    id: "veo-3.1-generate-preview",
    name: "Google Veo 3.1 (Cinematic & Audio)",
    supportedResolutions: ["720p", "1080p", "4k"],
    supportedAspectRatios: ["16:9", "9:16"],
    supportedDurations: [8],
    defaultDuration: 8,
    maxReferenceImages: 3,
    supportsKeyframes: true,
    nativeAudio: true,
    notes: "State-of-the-art 8s video with native sound, keyframe interpolation (0, 1, or 2 frames), and character anchors.",
  },
  "veo-3.0-generate-001": {
    id: "veo-3.0-generate-001",
    name: "Veo 3.0 Standard",
    supportedResolutions: ["720p", "1080p"],
    supportedAspectRatios: ["16:9"],
    supportedDurations: [8],
    defaultDuration: 8,
    maxReferenceImages: 1,
    supportsKeyframes: false,
    nativeAudio: true,
    notes: "Previous-generation standard Veo model.",
  },
  "veo-3.0-fast-generate-001": {
    id: "veo-3.0-fast-generate-001",
    name: "Veo 3.0 Fast",
    supportedResolutions: ["720p"],
    supportedAspectRatios: ["16:9"],
    supportedDurations: [8],
    defaultDuration: 8,
    maxReferenceImages: 1,
    supportsKeyframes: false,
    nativeAudio: true,
    notes: "Optimized for velocity and rapid creative iterations.",
  },
};

export const IMAGE_MODELS: Record<string, ImageModelSpec> = {
  "gemini-nano-banana-2.1": {
    id: "gemini-nano-banana-2.1",
    name: "Nano Banana 2.1 (Recommended)",
    supportedSizes: ["1K", "2K", "4K"],
    supportedAspectRatios: ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
    supportsGoogleSearch: true,
    maxReferenceImages: 14,
    maxCharacterReferences: 4,
    notes: "Primary high-efficiency model with search grounding, multi-turn consistency, and 4K resolution.",
  },
  "gemini-3-pro-image": {
    id: "gemini-3-pro-image",
    name: "Nano Banana Pro (Premium & Typography)",
    supportedSizes: ["1K", "2K", "4K"],
    supportedAspectRatios: ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
    supportsGoogleSearch: true,
    maxReferenceImages: 14,
    maxCharacterReferences: 5,
    notes: "Premium model for complex scenes, typography rendering, brand consistency, and reference mixing.",
  },
  "gemini-3.1-flash-image": {
    id: "gemini-3.1-flash-image",
    name: "Nano Banana 2 (Flash Image)",
    supportedSizes: ["512px", "1K", "2K", "4K"],
    supportedAspectRatios: ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
    supportsGoogleSearch: true,
    maxReferenceImages: 14,
    maxCharacterReferences: 4,
    notes: "Balanced workhorse supporting fast 512px previews through 4K.",
  },
  "gemini-3.1-flash-lite-image": {
    id: "gemini-3.1-flash-lite-image",
    name: "Nano Banana 2 Lite (Ultra Fast)",
    supportedSizes: ["1K"],
    supportedAspectRatios: ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
    supportsGoogleSearch: false,
    maxReferenceImages: 14,
    maxCharacterReferences: 0,
    notes: "Fastest and lowest-cost model. Fixed to 1K resolution, no search grounding.",
  },
  "gemini-2.5-flash-image": {
    id: "gemini-2.5-flash-image",
    name: "Nano Banana Legacy (Gemini 2.5)",
    supportedSizes: ["1K"],
    supportedAspectRatios: ["1:1", "16:9", "9:16"],
    supportsGoogleSearch: false,
    maxReferenceImages: 4,
    maxCharacterReferences: 1,
    notes: "Legacy pioneer image model.",
  },
};

export const ASPECT_RATIOS = [
  { label: "16:9 Landscape", value: "16:9", icon: "aspect-16-9" },
  { label: "9:16 Portrait / Reel", value: "9:16", icon: "aspect-9-16" },
  { label: "1:1 Square", value: "1:1", icon: "aspect-1-1" },
  { label: "4:3 Standard Photo", value: "4:3", icon: "aspect-4-3" },
  { label: "3:4 Vertical Photo", value: "3:4", icon: "aspect-3-4" },
  { label: "3:2 Classic 35mm", value: "3:2", icon: "aspect-3-2" },
  { label: "2:3 Vertical 35mm", value: "2:3", icon: "aspect-2-3" },
  { label: "4:5 Social Portrait", value: "4:5", icon: "aspect-4-5" },
  { label: "5:4 Landscape", value: "5:4", icon: "aspect-5-4" },
  { label: "21:9 Ultra-Wide", value: "21:9", icon: "aspect-21-9" },
];

