import { NextRequest, NextResponse } from "next/server";
import { mcpManager } from "@/lib/mcp-client";
import path from "path";
import fs from "fs";

export async function GET(req: NextRequest) {
  try {
    const rootDir = path.resolve(process.cwd(), "..");
    const opsFile = path.join(rootDir, "active_operations.json");
    let operationsList: any[] = [];

    if (fs.existsSync(opsFile)) {
      try {
        const data = JSON.parse(fs.readFileSync(opsFile, "utf-8"));
        operationsList = Object.values(data);
      } catch (e) {
        console.error("Error reading active operations file:", e);
      }
    }

    const searchParams = req.nextUrl.searchParams;
    const filter = searchParams.get("filter");
    if (filter && filter !== "ALL") {
      operationsList = operationsList.filter(
        (op) => (op.status || "").toUpperCase() === filter.toUpperCase()
      );
    }

    // Sort descending by created_at
    operationsList.sort((a, b) => {
      const tA = new Date(a.created_at || 0).getTime();
      const tB = new Date(b.created_at || 0).getTime();
      return tB - tA;
    });

    return NextResponse.json({
      success: true,
      operations: operationsList,
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
    const { operation_name, output_path } = body;

    if (!operation_name) {
      return NextResponse.json(
        { success: false, error: "operation_name is required" },
        { status: 400 }
      );
    }

    const checkRes = await mcpManager.callTool("check_video_operation", {
      operation_name,
      output_path,
    });

    // Re-read updated operation
    const rootDir = path.resolve(process.cwd(), "..");
    const opsFile = path.join(rootDir, "active_operations.json");
    let updatedOp = null;
    if (fs.existsSync(opsFile)) {
      try {
        const data = JSON.parse(fs.readFileSync(opsFile, "utf-8"));
        updatedOp = data[operation_name] || null;
      } catch (e) {}
    }

    return NextResponse.json({
      success: checkRes.success,
      content: checkRes.content,
      operation: updatedOp,
    });
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || String(err) },
      { status: 500 }
    );
  }
}

