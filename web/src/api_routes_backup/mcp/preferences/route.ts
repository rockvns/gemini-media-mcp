import { NextRequest, NextResponse } from "next/server";
import { mcpManager } from "@/lib/mcp-client";
import path from "path";
import fs from "fs";

export async function GET() {
  try {
    const rootDir = path.resolve(process.cwd(), "..");
    const prefFile = path.join(rootDir, "user_preferences.json");
    let rawPreferences = {
      output_dir: null,
      video: null,
      image: null,
    };

    if (fs.existsSync(prefFile)) {
      try {
        rawPreferences = JSON.parse(fs.readFileSync(prefFile, "utf-8"));
      } catch (e) {
        console.error("Error reading preferences file:", e);
      }
    }

    const summaryRes = await mcpManager.callTool("get_user_preferences", {});

    return NextResponse.json({
      success: true,
      preferences: rawPreferences,
      summary: summaryRes.content,
    });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || String(err) },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    // Pass args directly to set_user_preferences
    const res = await mcpManager.callTool("set_user_preferences", body);

    const rootDir = path.resolve(process.cwd(), "..");
    const prefFile = path.join(rootDir, "user_preferences.json");
    let updatedPreferences = null;
    if (fs.existsSync(prefFile)) {
      try {
        updatedPreferences = JSON.parse(fs.readFileSync(prefFile, "utf-8"));
      } catch (e) {}
    }

    return NextResponse.json({
      success: res.success,
      content: res.content,
      preferences: updatedPreferences,
    });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || String(err) },
      { status: 500 }
    );
  }
}

export async function DELETE() {
  try {
    const res = await mcpManager.callTool("reset_user_preferences", {});

    const rootDir = path.resolve(process.cwd(), "..");
    const prefFile = path.join(rootDir, "user_preferences.json");
    let resetPreferences = null;
    if (fs.existsSync(prefFile)) {
      try {
        resetPreferences = JSON.parse(fs.readFileSync(prefFile, "utf-8"));
      } catch (e) {}
    }

    return NextResponse.json({
      success: res.success,
      content: res.content,
      preferences: resetPreferences,
    });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || String(err) },
      { status: 500 }
    );
  }
}

