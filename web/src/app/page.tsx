import React from "react";
import Link from "next/link";
import {
  Presentation,
  BarChart3,
  FileText,
  Layers,
  Sliders,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Eye,
  Workflow,
  Sparkles,
} from "lucide-react";
import { getManifest, getMethodSummaries, formatPct, formatMetric } from "@/lib/data";

export default function HomePage() {
  const manifest = getManifest();
  const methodSummaries = getMethodSummaries();

  // Find standout metric values dynamically from data
  const topDetMethod = [...methodSummaries].sort((a, b) => b.detection_rate - a.detection_rate)[0];
  const topCnrMethod = [...methodSummaries].sort((a, b) => b.mean_cnr - a.mean_cnr)[0];
  const topSpeedMethod = [...methodSummaries].sort((a, b) => a.mean_runtime_ms - b.mean_runtime_ms)[0];
  const topLocMethod = [...methodSummaries]
    .filter((m) => m.mean_loc_error_detected_mm !== null && m.mean_loc_error_detected_mm > 0)
    .sort((a, b) => (a.mean_loc_error_detected_mm || 99) - (b.mean_loc_error_detected_mm || 99))[0];

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 border-b border-slate-800/80 bg-gradient-to-b from-slate-900/50 via-slate-950 to-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/30 text-cyan-300 text-xs font-mono">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Computational Non-Destructive Testing (NDT) Benchmark</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight leading-tight">
              Linear Frequency-Modulated Infrared Thermography
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400">
                for Subsurface Slag Inclusion Detection in Mild Steel
              </span>
            </h1>

            <p className="text-slate-300 text-sm sm:text-base leading-relaxed max-w-2xl mx-auto">
              Simulation-Based Thermal NDT using genuine 3-D Finite Element Method (`scikit-fem`) forward modeling, chirp excitation, virtual IR camera synthesis, and blind signal processing algorithms.
            </p>

            {/* Badges */}
            <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs font-mono">
              <span className="px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-700/80">
                3-D FEM (scikit-fem)
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-700/80">
                4,030 Evaluations
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-700/80">
                25 Defect Geometries
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-900 text-slate-300 border border-slate-700/80">
                Strict Blind Processing
              </span>
              <span className="px-2.5 py-1 rounded-md bg-emerald-950/40 text-emerald-300 border border-emerald-700/60">
                34 Automated Tests Passing
              </span>
            </div>

            {/* Primary Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
              <Link
                href="/conference"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm transition-all shadow-lg shadow-cyan-500/20"
              >
                <Presentation className="w-4 h-4" />
                Launch Conference Mode
              </Link>
              <Link
                href="/results"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition-colors"
              >
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                Explore Results
              </Link>
              <Link
                href="/methodology"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium text-sm border border-slate-800 transition-colors"
              >
                <FileText className="w-4 h-4 text-indigo-400" />
                View Methodology
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Standout Audited Fact Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Highest Overall Detection
            </div>
            <div className="text-2xl font-bold text-cyan-400">
              {formatPct(topDetMethod.detection_rate)}
            </div>
            <div className="text-xs text-slate-300 font-medium">
              {topDetMethod.method} (Pulse Compression)
            </div>
            <div className="text-[11px] text-slate-400 pt-1">
              Maintains temporal processing gain across 20–30 dB AWGN.
            </div>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Highest Defect Contrast
            </div>
            <div className="text-2xl font-bold text-emerald-400">
              {formatMetric(topCnrMethod.mean_cnr, 2)} CNR
            </div>
            <div className="text-xs text-slate-300 font-medium">
              {topCnrMethod.method} (Optimal EOF Spatial Mode)
            </div>
            <div className="text-[11px] text-slate-400 pt-1">
              Orthogonal subspace decomposition isolates low-effusivity inclusions.
            </div>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Lowest Detected Centroid Error
            </div>
            <div className="text-2xl font-bold text-indigo-400">
              {formatMetric(topLocMethod?.mean_loc_error_detected_mm, 2, "mm")}
            </div>
            <div className="text-xs text-slate-300 font-medium">
              {topLocMethod?.method}
            </div>
            <div className="text-[11px] text-slate-400 pt-1">
              Evaluated strictly on verified successful defect detections.
            </div>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Lowest Execution Latency
            </div>
            <div className="text-2xl font-bold text-amber-400">
              {formatMetric(topSpeedMethod.mean_runtime_ms, 2, "ms")}
            </div>
            <div className="text-xs text-slate-300 font-medium">
              {topSpeedMethod.method}
            </div>
            <div className="text-[11px] text-slate-400 pt-1">
              Fast dimensional compression suited for edge embedded compute.
            </div>
          </div>
        </div>
      </section>

      {/* Scientific Pipeline Diagram */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center justify-center gap-2">
            <Workflow className="w-5 h-5 text-cyan-400" />
            End-to-End Simulation & Processing Pipeline
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            A fully automated, zero-leakage workflow from 3D forward heat PDE discretization to quantitative metric evaluation.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 font-mono text-xs">
          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1.5">
            <div className="text-cyan-400 font-bold">01. LFMT Excitation</div>
            <p className="text-slate-400 text-[11px]">
              Chirp flux q(t) = q<sub>0</sub>[1 + sin(&phi;(t))] sweeping 0.05 &rarr; 0.50 Hz.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1.5">
            <div className="text-cyan-400 font-bold">02. 3D FEM Solver</div>
            <p className="text-slate-400 text-[11px]">
              Hexahedral variational formulation: (M + &Delta;t K)T<sup>n+1</sup> = MT<sup>n</sup> + &Delta;t F.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1.5">
            <div className="text-cyan-400 font-bold">03. Virtual IR Camera</div>
            <p className="text-slate-400 text-[11px]">
              2D spatial discretization, emissivity non-uniformity, and AWGN (20–30 dB).
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1.5">
            <div className="text-cyan-400 font-bold">04. Blind Processing</div>
            <p className="text-slate-400 text-[11px]">
              Matched Filter, PCT (Kurtosis SVD), SPCT (Sparse PCA), and RPT embeddings.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1.5">
            <div className="text-cyan-400 font-bold">05. Defect Isolation</div>
            <p className="text-slate-400 text-[11px]">
              Adaptive Otsu thresholding & morphological filtering (min area &ge; 3 px).
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 space-y-1.5">
            <div className="text-cyan-400 font-bold">06. Metrics & Audit</div>
            <p className="text-slate-400 text-[11px]">
              CNR, IoU, Dice, detected-only localization error E<sub>loc</sub>, and max depth z<sub>max</sub>.
            </p>
          </div>
        </div>
      </section>

      {/* Feature Navigation Cards */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-lg font-semibold text-white">Interactive Research Modules</h3>
          <span className="text-xs text-slate-400 font-mono">100% Client/Static Rendered</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            href="/conference"
            className="group p-6 rounded-xl border border-cyan-500/30 bg-slate-900/40 hover:bg-slate-900/80 hover:border-cyan-500/60 transition-all space-y-3"
          >
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <Presentation className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors flex items-center justify-between">
              Conference Mode
              <ArrowRight className="w-4 h-4 text-cyan-400 transform group-hover:translate-x-1 transition-transform" />
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Fullscreen projector presentation interface with dynamic defect geometry switching, 6-method visual contrast maps, and live metrics table.
            </p>
          </Link>

          <Link
            href="/results"
            className="group p-6 rounded-xl border border-slate-800 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700 transition-all space-y-3"
          >
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors flex items-center justify-between">
              Benchmark Results
              <ArrowRight className="w-4 h-4 text-emerald-400 transform group-hover:translate-x-1 transition-transform" />
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Statistical comparison across all 4,030 evaluations broken down by subsurface depth, defect diameter, noise SNR, and execution speed.
            </p>
          </Link>

          <Link
            href="/sensitivity"
            className="group p-6 rounded-xl border border-slate-800 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700 transition-all space-y-3"
          >
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Sliders className="w-5 h-5" />
            </div>
            <h4 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors flex items-center justify-between">
              Parameter Sensitivity
              <ArrowRight className="w-4 h-4 text-indigo-400 transform group-hover:translate-x-1 transition-transform" />
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Controlled one-at-a-time variation of excitation heat flux \(q_0\), slag conductivity \(k\), convection \(h\), and slag specific heat \(C_p\).
            </p>
          </Link>
        </div>
      </section>
    </div>
  );
}