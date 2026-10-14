import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import path from "path";
import fs from "fs";

export interface McpToolResponse {
  success: boolean;
  content: string;
  error?: string;
  raw?: any;
}

class McpManager {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;
  private isConnecting = false;
  private connectPromise: Promise<Client> | null = null;

  private getEnvironment(): Record<string, string> {
    const rootDir = path.resolve(process.cwd(), "..");
    const envVars: Record<string, string> = { ...process.env as Record<string, string> };

    // 1. Check root .env (d:\work\MCP\google-flow\.env)
    const rootEnvPath = path.join(rootDir, ".env");
    if (fs.existsSync(rootEnvPath)) {
      const content = fs.readFileSync(rootEnvPath, "utf-8");
      for (const line of content.split("\n")) {
        const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
        if (match) {
          const key = match[1];
          const val = match[2]?.trim().replace(/^['"]|['"]$/g, "") || "";
          envVars[key] = val;
        }
      }
    }

    // 2. Check web/.env.local or web/.env
    const localEnvPath = path.resolve(process.cwd(), ".env.local");
    if (fs.existsSync(localEnvPath)) {
      const content = fs.readFileSync(localEnvPath, "utf-8");
      for (const line of content.split("\n")) {
        const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
        if (match) {
          const key = match[1];
          const val = match[2]?.trim().replace(/^['"]|['"]$/g, "") || "";
          envVars[key] = val;
        }
      }
    }

    // 3. Fallback to IDE MCP configuration (~/.gemini/config/mcp_config.json)
    if (!envVars["GEMINI_API_KEY"]) {
      const homeDir = process.env.USERPROFILE || process.env.HOME || "";
      const mcpConfigPath = path.join(homeDir, ".gemini", "config", "mcp_config.json");
      if (fs.existsSync(mcpConfigPath)) {
        try {
          const parsed = JSON.parse(fs.readFileSync(mcpConfigPath, "utf-8"));
          const serverEnv = parsed.mcpServers?.["gemini-media-mcp"]?.env;
          if (serverEnv?.GEMINI_API_KEY) {
            envVars["GEMINI_API_KEY"] = serverEnv.GEMINI_API_KEY;
          }
        } catch (e) {}
      }
    }

    return envVars;
  }

  public async getClient(): Promise<Client> {
    if (this.client) {
      return this.client;
    }

    if (this.isConnecting && this.connectPromise) {
      return this.connectPromise;
    }

    this.isConnecting = true;
    this.connectPromise = (async () => {
      try {
        const rootDir = path.resolve(process.cwd(), "..");
        const pythonPath = path.join(rootDir, ".venv", "Scripts", "python.exe");
        const scriptPath = path.join(rootDir, "gemini_mcp.py");

        if (!fs.existsSync(pythonPath)) {
          throw new Error(`Python virtual environment not found at: ${pythonPath}`);
        }
        if (!fs.existsSync(scriptPath)) {
          throw new Error(`MCP entry script not found at: ${scriptPath}`);
        }

        const envVars = this.getEnvironment();

        this.transport = new StdioClientTransport({
          command: pythonPath,
          args: [scriptPath],
          env: envVars,
          cwd: rootDir,
        });

        const client = new Client(
          { name: "NextJsStudioClient", version: "2.0.0" },
          { capabilities: {} }
        );

        await client.connect(this.transport);
        this.client = client;
        this.isConnecting = false;
        return client;
      } catch (err) {
        this.isConnecting = false;
        this.client = null;
        this.connectPromise = null;
        throw err;
      }
    })();

    return this.connectPromise;
  }

  public async callTool(name: string, args: Record<string, any> = {}): Promise<McpToolResponse> {
    try {
      const client = await this.getClient();
      const res = await client.callTool({
        name,
        arguments: args,
      });

      const text = (res.content as any[])
        ?.map((item: any) => item.text || "")
        .filter(Boolean)
        .join("\n") || "";

      return {
        success: !res.isError,
        content: text,
        raw: res,
      };
    } catch (err: any) {
      // If error occurred due to closed transport, reset client so next call reconnects
      this.client = null;
      this.connectPromise = null;
      return {
        success: false,
        content: err?.message || String(err),
        error: err?.message || String(err),
      };
    }
  }

  public async listTools() {
    const client = await this.getClient();
    return await client.listTools();
  }

  public async listResources() {
    const client = await this.getClient();
    return await client.listResources();
  }

  public async readResource(uri: string) {
    const client = await this.getClient();
    return await client.readResource({ uri });
  }

  public async listPrompts() {
    const client = await this.getClient();
    return await client.listPrompts();
  }

  public async getPrompt(name: string, args: Record<string, any> = {}) {
    const client = await this.getClient();
    return await client.getPrompt({ name, arguments: args });
  }
}

// Global singleton instance for Next.js server runtime
const globalForMcp = globalThis as unknown as { mcpManager?: McpManager };
export const mcpManager = globalForMcp.mcpManager ?? new McpManager();
if (process.env.NODE_ENV !== "production") {
  globalForMcp.mcpManager = mcpManager;
}
