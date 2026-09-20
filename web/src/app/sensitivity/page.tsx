import React from "react";
import { Sliders, HelpCircle, AlertCircle } from "lucide-react";
import { getSensitivityRecords, formatMetric } from "@/lib/data";
import { SensitivityBarChart } from "@/components/charts/SensitivityBarChart";

export default function SensitivityPage() {
  const records = getSensitivityRecords();

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs">
          <Sliders className="w-4 h-4" />
          <span>PARAMETRIC STUDY</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Controlled Parameter Sensitivity Analysis
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          One-at-a-time variation of physical excitation flux q<sub>0</sub>, slag inclusion thermal conductivity k<sub>slag</sub>, convection coefficient h<sub>conv</sub>, and specific heat C<sub>p,slag</sub> on representative geometry (D = 8.0 mm, z = 0.4 mm).
        </p>
      </div>

      {/* Disambiguation Banner */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3 text-xs text-slate-300">
        <AlertCircle className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
        <div className="space-y-1">
          <strong className="text-slate-100">Thermal Nomenclature Distinction:</strong>
          <p className="text-slate-400">
            &bull; <strong>Peak Surface Temperature Rise above Ambient (&Delta;T<sub>surf,max</sub>):</strong> Maximum elevation of front plate temperature above ambient (T - T<sub>amb</sub> &asymp; 6.915 K). Scales linearly with incident flux q<sub>0</sub>.<br />
            &bull; <strong>Peak Defect Thermal Contrast (&Delta;T<sub>defect,max</sub>):</strong> Maximum surface differential between inclusion center and sound plate (max |T<sub>defect</sub> - T<sub>sound</sub>| &asymp; 0.6151 K).
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
        <h3 className="text-xs font-mono uppercase text-slate-300 font-semibold">
          Surface Temperature Response across PDE Parameter Variations
        </h3>
        <SensitivityBarChart data={records} />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
        <h3 className="text-xs font-mono uppercase text-slate-200 font-semibold border-b border-slate-800 pb-2">
          Parametric Sensitivity Quantitative Results (D = 8.0 mm, z = 0.4 mm, Clean)
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300 font-mono">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-2.5">Variation</th>
                <th className="px-3 py-2.5">Parameter</th>
                <th className="px-3 py-2.5 text-center">\(\Delta [\%]\)</th>
                <th className="px-3 py-2.5 text-right">Peak Temp Rise [K]</th>
                <th className="px-3 py-2.5 text-right">Defect Contrast [K]</th>
                <th className="px-3 py-2.5 text-right">PCT CNR</th>
                <th className="px-3 py-2.5 text-center">Detected</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {records.map((r, i) => (
                <tr key={i} className="hover:bg-slate-950/40">
                  <td className="px-3 py-2.5 font-bold text-slate-200">{r.variation}</td>
                  <td className="px-3 py-2.5 text-slate-400">{r.parameter}</td>
                  <td className="px-3 py-2.5 text-center">{r.percentage_change > 0 ? `+${r.percentage_change}%` : `${r.percentage_change}%`}</td>
                  <td className="px-3 py-2.5 text-right font-semibold text-cyan-300">{formatMetric(r.peak_surface_temp_rise_k, 3)} K</td>
                  <td className="px-3 py-2.5 text-right font-semibold text-indigo-300">{formatMetric(r.peak_defect_thermal_contrast_k, 4)} K</td>
                  <td className="px-3 py-2.5 text-right font-semibold text-emerald-400">{formatMetric(r.pct_cnr, 3)}</td>
                  <td className="px-3 py-2.5 text-center text-slate-400">{r.is_detected ? "YES" : "NO (Clean)"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}