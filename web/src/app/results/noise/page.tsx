import React from "react";
import Link from "next/link";
import { Activity, ArrowLeft, AlertCircle } from "lucide-react";
import { getNoiseSummaries, getHealthySummaries, formatMetric, formatPct } from "@/lib/data";
import { NoiseLineChart } from "@/components/charts/NoiseLineChart";

export default function NoiseRobustnessPage() {
  const noiseSummaries = getNoiseSummaries();
  const healthySummaries = getHealthySummaries();

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <Link href="/results" className="inline-flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Results
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Noise Robustness & Healthy Control Specificity
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Evaluates algorithm performance degradation under additive white Gaussian noise (Clean, 30 dB, 25 dB, 20 dB SNR) across 10 deterministic noise realizations per scenario.
        </p>
      </div>

      {/* Note Callout */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3 text-xs text-slate-300">
        <AlertCircle className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
        <p className="leading-relaxed">
          <strong>Blind Mode Segmentation Note:</strong> In clean, uncorrupted conditions, PCT produces an extremely high evaluation CNR (&gt; 26) but perfectly flat background mode, which causes Otsu adaptive thresholding to reject the background without segmenting. Under realistic sensor noise (30 dB), spatial noise perturbs the SVD mode and enables robust low-millimeter blind localization (1.70 mm).
        </p>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Detection Success Rate across Noise Levels
          </h3>
          <NoiseLineChart data={noiseSummaries} metricKey="detection_rate" metricLabel="Detection Rate" unit="%" isPercent />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Contrast-to-Noise Ratio (CNR) across Noise Levels
          </h3>
          <NoiseLineChart data={noiseSummaries} metricKey="mean_cnr" metricLabel="Mean CNR" />
        </div>
      </div>

      {/* Healthy Control Specificity Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="text-xs font-mono uppercase text-slate-200 font-semibold">
            Healthy Control Specimen (D = 0 mm) Specificity & False Alarm Rate
          </h3>
          <span className="text-[11px] font-mono text-slate-400">155 Evaluations</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300 font-mono">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-2.5">Method</th>
                <th className="px-3 py-2.5">Condition</th>
                <th className="px-3 py-2.5 text-center">Evaluations</th>
                <th className="px-3 py-2.5 text-center">False Alarms</th>
                <th className="px-3 py-2.5 text-right">False Alarm Rate</th>
                <th className="px-3 py-2.5 text-right">Specificity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {healthySummaries.map((h, i) => (
                <tr key={`${h.method}-${h.noise_condition}-${i}`} className="hover:bg-slate-950/40">
                  <td className="px-3 py-2 font-semibold text-slate-200">{h.method}</td>
                  <td className="px-3 py-2 text-slate-400">{h.noise_condition}</td>
                  <td className="px-3 py-2 text-center">{h.total_evaluations}</td>
                  <td className="px-3 py-2 text-center">{h.false_positive_count}</td>
                  <td className="px-3 py-2 text-right">{formatPct(h.false_positive_rate)}</td>
                  <td className="px-3 py-2 text-right font-bold text-emerald-400">{formatPct(h.specificity_pct)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}