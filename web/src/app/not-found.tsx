import React from "react";
import Link from "next/link";
import { Home, Flame, Presentation, FileText, Compass } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center space-y-6 bg-slate-900/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-sm shadow-2xl">
        <div className="inline-flex p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
          <Compass className="w-8 h-8 animate-spin-slow" />
        </div>

        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold text-white tracking-tight font-mono">404</h1>
          <h2 className="text-lg font-semibold text-slate-200">LFMT Research Portal — Page Not Found</h2>
          <p className="text-xs text-slate-400">
            The requested route does not exist or has been relocated within the research workspace.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2">
          <Link
            href="/"
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all"
          >
            <Home className="w-3.5 h-3.5" />
            Home
          </Link>
          <Link
            href="/simulate"
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-semibold border border-amber-500/40 transition-all"
          >
            <Flame className="w-3.5 h-3.5" />
            Simulation
          </Link>
          <Link
            href="/conference"
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs font-semibold border border-cyan-500/40 transition-all"
          >
            <Presentation className="w-3.5 h-3.5" />
            Conference
          </Link>
        </div>
      </div>
    </div>
  );
}
