import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs";

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

export async function GET(req: NextRequest) {
  try {
    const rootDir = path.resolve(process.cwd(), "..");
    const outputsDir = path.join(rootDir, "outputs");
    const opsFile = path.join(rootDir, "active_operations.json");

    if (!fs.existsSync(outputsDir)) {
      return NextResponse.json({ success: true, assets: [] });
    }

    // Load active operations map for metadata matching
    let opsMap: Record<string, any> = {};
    if (fs.existsSync(opsFile)) {
      try {
        const raw = JSON.parse(fs.readFileSync(opsFile, "utf-8"));
        for (const op of Object.values(raw) as any[]) {
          if (op.output_path) {
            const base = path.basename(op.output_path);
            opsMap[base] = op;
          }
        }
      } catch (e) {}
    }

    const scanDir = (dir: string, baseRelative = ""): MediaAsset[] => {
      const results: MediaAsset[] = [];
      const entries = fs.readdirSync(dir, { withFileTypes: true });

      for (const entry of entries) {
        const rel = baseRelative ? `${baseRelative}/${entry.name}` : entry.name;
        const full = path.join(dir, entry.name);

        if (entry.isDirectory()) {
          // Scan uploads subdirectory too
          results.push(...scanDir(full, rel));
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase();
          if ([".mp4", ".png", ".jpg", ".jpeg", ".webp"].includes(ext)) {
            const stat = fs.statSync(full);
            const isVideo = ext === ".mp4";
            const matchedOp = opsMap[entry.name];

            results.push({
              filename: entry.name,
              relativePath: rel,
              absolutePath: full,
              url: `/api/media/${rel.split("/").map(encodeURIComponent).join("/")}`,
              type: isVideo ? "video" : "image",
              size: stat.size,
              createdAt: stat.birthtime ? stat.birthtime.toISOString() : stat.mtime.toISOString(),
              model: matchedOp?.model,
              prompt: matchedOp?.prompt,
              aspectRatio: matchedOp?.aspect_ratio,
              resolution: matchedOp?.resolution,
            });
          }
        }
      }
      return results;
    };

    const assets = scanDir(outputsDir);

    // Sort newest first
    assets.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());

    const typeFilter = req.nextUrl.searchParams.get("type");
    const filtered = typeFilter && typeFilter !== "all"
      ? assets.filter((a) => a.type === typeFilter)
      : assets;

    return NextResponse.json({
      success: true,
      assets: filtered,
    });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || String(err) },
      { status: 500 }
    );
  }
}

