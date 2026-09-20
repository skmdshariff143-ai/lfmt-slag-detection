import React from "react";
import Link from "next/link";
import { Disc, ArrowLeft } from "lucide-react";
import { getDiameterSummaries, getMaxDepthRecords, formatMetric, formatPct } from "@/lib/data";
import { DiameterLineChart } from "@/components/charts/DiameterLineChart";
import { MaxDepthMatrix } from "@/components/charts/MaxDepthMatrix";

export default function DiameterAnalysisPage() {
  const diameterSummaries = getDiameterSummaries();
  const maxDepthRecords = getMaxDepthRecords();

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <Link href="/results" className="inline-flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Results
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Defect Diameter & Sizing Analysis (D &isin; [4.0, 12.0] mm)
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Larger inclusions present a wider cross-sectional thermal barrier, generating stronger surface temperature differentials and enabling deeper subsurface detection reach.
        </p>
      </div>

      {/* Maximum Detectable Depth Matrix */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="text-xs font-mono uppercase text-slate-200 font-semibold">
            Maximum Detectable Depth Matrix (z<sub>max</sub> satisfying Detection &ge; 80% at SNR = 30 dB)
          </h3>
          <span className="text-[11px] font-mono text-slate-400">80% Criterion</span>
        </div>
        <MaxDepthMatrix data={maxDepthRecords} selectedNoise="SNR 30 dB" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Detection Success Rate vs Defect Diameter
          </h3>
          <DiameterLineChart data={diameterSummaries} metricKey="detection_rate" metricLabel="Detection Rate" unit="%" isPercent />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Contrast-to-Noise Ratio (CNR) vs Defect Diameter
          </h3>
          <DiameterLineChart data={diameterSummaries} metricKey="mean_cnr" metricLabel="Mean CNR" />
        </div>
      </div>
    </div>
  );
}