import { NextRequest, NextResponse } from "next/server";
import { mcpManager } from "@/lib/mcp-client";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { tool, args = {} } = body;

    if (!tool) {
      return NextResponse.json({ success: false, error: "Tool name is required" }, { status: 400 });
    }

    const response = await mcpManager.callTool(tool, args);
    return NextResponse.json(response);
  } catch (err: any) {
    return NextResponse.json(
      {
        success: false,
        error: err?.message || String(err),
      },
      { status: 500 }
    );
  }
}

