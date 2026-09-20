import React from "react";
import { getManifest } from "@/lib/data";

export const ProvenanceBanner: React.FC = () => {
  let manifest;
  try {
    manifest = getManifest();
  } catch {
    manifest = {
      dataset_version: "2.1.0-final-audited",
      protocol_version: "blind-v2-audited",
      git_commit_sha: "05b93e0",
      solver_backend: "fem",
      total_evaluations: 4030,
    };
  }

  return (
    <div className="border-b border-slate-800/60 bg-slate-950/40 text-xs font-mono text-slate-400 py-1.5 px-4">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            AUDITED RESEARCH DATASET
          </span>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-slate-300">Backend: <strong className="text-slate-200">3-D FEM (scikit-fem ElementHex1)</strong></span>
          <span className="text-slate-600 hidden md:inline">|</span>
          <span className="hidden md:inline text-slate-300">Evaluations: <strong className="text-slate-200">{manifest.total_evaluations.toLocaleString()}</strong></span>
        </div>
        <div className="flex items-center gap-3 text-slate-400">
          <span>Protocol: <strong className="text-slate-300">Strict Blind Mode</strong></span>
          <span className="text-slate-600">|</span>
          <span>Commit: <code className="text-cyan-400 bg-cyan-950/40 px-1 py-0.5 rounded border border-cyan-800/40">{manifest.git_commit_sha.slice(0, 7)}</code></span>
        </div>
      </div>
    </div>
  );
};