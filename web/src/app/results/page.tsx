import React from "react";
import Link from "next/link";
import {
  BarChart3,
  Layers,
  Activity,
  Maximize2,
  TrendingUp,
  Clock,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { getMethodSummaries, formatMetric, formatPct, METHOD_COLORS } from "@/lib/data";
import { MethodBarChart } from "@/components/charts/MethodBarChart";

export default function ResultsOverviewPage() {
  const summaries = getMethodSummaries();

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs">
          <BarChart3 className="w-4 h-4" />
          <span>BENCHMARK SYNTHESIS</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Comprehensive Algorithmic Benchmark (4,030 Evaluations)
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Statistical aggregation over 25 physical defect geometries (5 diameters × 5 depths) and 1 healthy control specimen across Clean, 30 dB, 25 dB, and 20 dB AWGN with 10 deterministic noise seeds.
        </p>
      </div>

      {/* Sub-navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3 font-mono text-xs">
        <Link
          href="/results"
          className="px-3 py-1.5 rounded-md bg-slate-800 text-cyan-400 border border-slate-700 font-semibold"
        >
          Overall Comparison
        </Link>
        <Link
          href="/results/depth"
          className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
        >
          Depth Analysis (z)
        </Link>
        <Link
          href="/results/diameter"
          className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
        >
          Diameter Analysis (D)
        </Link>
        <Link
          href="/results/noise"
          className="px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-900 transition-colors"
        >
          Noise Robustness (SNR)
        </Link>
      </div>

      {/* Overall Comparison Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-semibold text-white font-mono uppercase tracking-wider">
            Overall Performance Metrics by Processing Method (775 Runs per Method)
          </h2>
          <span className="text-xs font-mono text-slate-400">Strict Blind Mode</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300 font-mono">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-[11px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-3">Method</th>
                <th className="px-3 py-3 text-center">Total Runs</th>
                <th className="px-3 py-3 text-right">Detection Rate</th>
                <th className="px-3 py-3 text-right">Mean CNR</th>
                <th className="px-3 py-3 text-right">Mean IoU</th>
                <th className="px-3 py-3 text-right">Mean Dice</th>
                <th className="px-3 py-3 text-right">Loc Error (Detected)</th>
                <th className="px-3 py-3 text-right">Execution Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {summaries.map((s) => (
                <tr key={s.method} className="hover:bg-slate-950/40 transition-colors">
                  <td className="px-3 py-3.5 font-bold text-slate-200" style={{ color: METHOD_COLORS[s.method] || "#fff" }}>
                    {s.method}
                  </td>
                  <td className="px-3 py-3.5 text-center text-slate-400">{s.total_runs}</td>
                  <td className="px-3 py-3.5 text-right font-semibold text-slate-100">
                    {formatPct(s.detection_rate)}
                  </td>
                  <td className="px-3 py-3.5 text-right font-semibold text-slate-100">
                    {formatMetric(s.mean_cnr, 3)}
                  </td>
                  <td className="px-3 py-3.5 text-right text-slate-300">
                    {formatMetric(s.mean_iou, 3)}
                  </td>
                  <td className="px-3 py-3.5 text-right text-slate-300">
                    {formatMetric(s.mean_dice, 3)}
                  </td>
                  <td className="px-3 py-3.5 text-right text-cyan-300 font-medium">
                    {s.mean_loc_error_detected_mm !== null
                      ? `${formatMetric(s.mean_loc_error_detected_mm, 2)} mm`
                      : "N/A"}
                  </td>
                  <td className="px-3 py-3.5 text-right text-slate-400 font-medium">
                    {formatMetric(s.mean_runtime_ms, 2)} ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Side-by-side Bar Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Overall Defect Detection Success Rate [%]
          </h3>
          <MethodBarChart data={summaries} metricKey="detection_rate" metricLabel="Detection Rate" unit="%" isPercent />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Mean Defect Contrast-to-Noise Ratio (CNR)
          </h3>
          <MethodBarChart data={summaries} metricKey="mean_cnr" metricLabel="Mean CNR" />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Mean Centroid Localization Error (Detected Cases) [mm]
          </h3>
          <MethodBarChart data={summaries} metricKey="mean_loc_error_detected_mm" metricLabel="Localization Error" unit=" mm" />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Computational Execution Time [ms]
          </h3>
          <MethodBarChart data={summaries} metricKey="mean_runtime_ms" metricLabel="Runtime" unit=" ms" />
        </div>
      </div>
    </div>
  );
}