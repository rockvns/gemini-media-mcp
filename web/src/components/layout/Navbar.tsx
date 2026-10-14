"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { Video, Image as ImageIcon, Activity, FolderHeart, Settings, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();
  const [activeOpsCount, setActiveOpsCount] = useState<number>(0);
  const [apiReady, setApiReady] = useState<boolean | null>(null);

  useEffect(() => {
    // Initial fetch of operations count and health
    const checkStatus = async () => {
      try {
        const opsRes = await fetch("/api/mcp/operations?filter=IN_PROGRESS");
        if (opsRes.ok) {
          const data = await opsRes.json();
          setActiveOpsCount(data.operations?.length || 0);
        }

        const healthRes = await fetch("/api/mcp/tool", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tool: "check_api_status", args: {} }),
        });
        if (healthRes.ok) {
          const hData = await healthRes.json();
          setApiReady(hData.success && !hData.content?.includes("Default Placeholder (INVALID)"));
        }
      } catch (e) {
        setApiReady(false);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { label: "Video Studio", href: "/video", icon: Video },
    { label: "Image Studio", href: "/image", icon: ImageIcon },
    {
      label: "Operations",
      href: "/operations",
      icon: Activity,
      badge: activeOpsCount > 0 ? activeOpsCount : null,
    },
    { label: "Gallery", href: "/gallery", icon: FolderHeart },
    { label: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[#1f2438] bg-[#0c0e18]/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/video" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 via-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-violet-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-[#0c0e18] rounded-[10px] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-violet-400 group-hover:text-cyan-300 transition-colors" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight">gemini-media-mcp</span>
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-violet-950/80 text-violet-400 border border-violet-800/60">
                Studio
              </span>
            </div>
            <p className="text-xs text-zinc-400">Veo 3.1 & Nano Banana</p>
          </div>
        </Link>

        {/* Navigation tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href === "/video" && pathname === "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-violet-600/20 text-violet-300 border border-violet-500/40 shadow-sm shadow-violet-500/10"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-[#151928]"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-violet-400" : "text-zinc-400"}`} />
                <span className="hidden md:inline">{item.label}</span>
                {item.badge !== null && item.badge !== undefined && (
                  <span className="inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-violet-500 text-white animate-pulse">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Status */}
        <div className="flex items-center gap-3">
          <Link
            href="/settings"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-[#111422] hover:border-zinc-700 transition-colors"
          >
            {apiReady === true ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-zinc-300 hidden sm:inline">MCP Ready</span>
              </>
            ) : apiReady === false ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-amber-300 hidden sm:inline">API Check</span>
              </>
            ) : (
              <span className="text-zinc-400 text-xs">Checking...</span>
            )}
          </Link>
        </div>
      </div>
    </header>
  );
}

