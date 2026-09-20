import React from "react";
import Link from "next/link";
import { Layers, ArrowLeft } from "lucide-react";
import { getDepthSummaries, formatMetric, formatPct, METHOD_COLORS } from "@/lib/data";
import { DepthLineChart } from "@/components/charts/DepthLineChart";

export default function DepthAnalysisPage() {
  const depthSummaries = getDepthSummaries();

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <Link href="/results" className="inline-flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Results
        </Link>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Subsurface Depth Sensitivity Analysis (z &isin; [0.2, 1.0] mm)
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Increasing inclusion depth attenuates and spatially diffuses surface thermal signatures. This section investigates the degradation rate across all 5 processing methods.
        </p>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Detection Success Rate vs Subsurface Depth
          </h3>
          <DepthLineChart data={depthSummaries} metricKey="detection_rate" metricLabel="Detection Rate" unit="%" isPercent />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Contrast-to-Noise Ratio (CNR) vs Depth
          </h3>
          <DepthLineChart data={depthSummaries} metricKey="mean_cnr" metricLabel="Mean CNR" />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Segmentation IoU vs Depth
          </h3>
          <DepthLineChart data={depthSummaries} metricKey="mean_iou" metricLabel="Mean IoU" />
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
            Centroid Localization Error (Detected) vs Depth [mm]
          </h3>
          <DepthLineChart data={depthSummaries} metricKey="mean_loc_error_detected_mm" metricLabel="Loc Error" unit=" mm" />
        </div>
      </div>
    </div>
  );
}