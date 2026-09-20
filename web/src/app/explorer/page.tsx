import React from "react";
import { getCaseIndex, getCaseManifest, formatMetric, formatPct } from "@/lib/data";
import { Layers, ShieldCheck, CheckCircle2, XCircle } from "lucide-react";

interface Props {
  searchParams: { case?: string; noise?: string };
}

export const metadata = {
  title: "Defect Explorer | LFMT Slag Detection",
  description: "Interactive single-case defect inspection with multi-method post-processing and noise scenario comparison.",
};

export default function ExplorerPage({ searchParams }: Props) {
  const caseIndex = getCaseIndex();
  const selectedCaseTag = searchParams.case || (caseIndex.length > 0 ? caseIndex[0].case_tag : "D080_Z004");
  const selectedNoise = searchParams.noise || "Clean";

  const caseManifest = getCaseManifest(selectedCaseTag);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sky-400 font-mono text-xs uppercase tracking-wider mb-2">
          <Layers className="w-4 h-4" />
          <span>Single-Case Inspection</span>
        </div>
        <h1 className="text-3xl font-bold text-slate-100">Defect Case Explorer</h1>
        <p className="text-slate-400 text-sm mt-1 max-w-3xl">
          Deep-dive inspection into specific mild steel slag inclusion cases across all 5 post-processing methods
          under variable synthetic Gaussian white noise levels.
        </p>
      </div>

      {/* Provenance Notice */}
      <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-400 space-y-1">
        <div className="font-semibold text-sky-400 font-mono flex items-center gap-1.5">
          <span>&bull; Single-Case Representative Inspection Note:</span>
        </div>
        <p className="leading-relaxed">
          The metrics and thermal maps below reflect individual representative runs (deterministic visual noise seed = 42).
          For statistical benchmark performance across 10 deterministic noise realizations (seeds 1001&ndash;1010) and 4,030 total evaluations,
          refer to the <a href="/results" className="text-sky-400 hover:underline">Results Overview</a> and <a href="/conference" className="text-sky-400 hover:underline">Conference Dashboard</a>.
        </p>
      </div>

      {/* Case Selector Grid / Pills */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider font-mono">
          Select Defect Geometry / Specimen
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {caseIndex.map((c) => {
            const isSelected = c.case_tag === selectedCaseTag;
            return (
              <a
                key={c.case_tag}
                href={`/explorer?case=${c.case_tag}&noise=${selectedNoise}`}
                className={`p-3 rounded-lg border text-center transition-all ${
                  isSelected
                    ? "bg-sky-500/20 border-sky-400 text-sky-200 shadow-md shadow-sky-500/10"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <div className="text-xs font-mono font-bold">{c.case_tag}</div>
                <div className="text-[11px] text-slate-400 mt-1">
                  {c.is_healthy ? (
                    <span className="text-emerald-400 font-medium">Healthy</span>
                  ) : (
                    `Ø${c.diameter_mm}mm @ ${c.depth_mm}mm`
                  )}
                </div>
              </a>
            );
          })}
        </div>
      </div>

      {caseManifest ? (
        <div className="space-y-8">
          {/* Specimen Ground Truth Details */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 uppercase font-mono">Specimen Type</div>
              <div className="text-lg font-bold text-slate-100 mt-1">
                {caseManifest.is_healthy ? "Healthy Control" : "Defective Plate"}
              </div>
              <div className="text-xs text-slate-400 mt-1">Mild Steel Plate (100×70×10 mm)</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 uppercase font-mono">Defect Diameter</div>
              <div className="text-lg font-bold text-sky-400 mt-1">
                {caseManifest.is_healthy ? "None" : `${caseManifest.diameter_mm} mm`}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {caseManifest.is_healthy ? "Homogeneous steel" : `Area: ${(Math.PI * Math.pow(caseManifest.diameter_mm / 2, 2)).toFixed(1)} mm²`}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 uppercase font-mono">Subsurface Depth</div>
              <div className="text-lg font-bold text-amber-400 mt-1">
                {caseManifest.is_healthy ? "None" : `${caseManifest.depth_mm} mm`}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {caseManifest.is_healthy ? "Full thickness: 10 mm" : `Aspect Ratio: ${(caseManifest.diameter_mm / (caseManifest.depth_mm || 1)).toFixed(1)}:1`}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 uppercase font-mono">True Centroid (x, y)</div>
              <div className="text-lg font-bold text-emerald-400 mt-1">
                {caseManifest.ground_truth.has_defect
                  ? `(${caseManifest.ground_truth.center_x_mm}, ${caseManifest.ground_truth.center_y_mm}) mm`
                  : "N/A (Uniform)"}
              </div>
              <div className="text-xs text-slate-400 mt-1">Plate Center = (50.0, 35.0) mm</div>
            </div>
          </div>

          {/* Thermogram Sequence Strip */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-100">LFMT Thermal Response Sequence</h3>
                <p className="text-xs text-slate-400">
                  10 s chirp heating window (0.1 Hz → 1.0 Hz linearly swept frequency).
                </p>
              </div>
              <a
                href={`/thermograms?case=${selectedCaseTag}`}
                className="text-xs text-sky-400 hover:text-sky-300 font-mono underline"
              >
                Open Animated Scrubber →
              </a>
            </div>

            <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
              {caseManifest.frames.map((f) => (
                <div key={f.frame_index} className="space-y-1 text-center bg-slate-950 p-1.5 rounded-lg border border-slate-800">
                  <div className="relative aspect-square w-full rounded overflow-hidden bg-slate-900">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={f.image_url}
                      alt={`Frame ${f.frame_index} at t=${f.time_seconds}s`}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>
                  <div className="text-[10px] font-mono text-slate-400">t={f.time_seconds}s</div>
                  <div className="text-[9px] font-mono text-slate-300">{f.max_temp_c.toFixed(1)}°C</div>
                </div>
              ))}
            </div>
          </div>

          {/* Noise Scenario Selector Tabs & Comparison Visualization */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-100">Multi-Method Comparison Maps</h3>
                <p className="text-xs text-slate-400">
                  Comparing raw contrast, matched filtering, PCT (EOF-2), SPCT, and RPT under selected noise.
                </p>
              </div>

              {/* Noise Level Switcher */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                {(["Clean", "30dB", "25dB", "20dB"] as const).map((lvl) => (
                  <a
                    key={lvl}
                    href={`/explorer?case=${selectedCaseTag}&noise=${lvl}`}
                    className={`px-3 py-1 rounded text-xs font-mono font-medium transition-all ${
                      selectedNoise === lvl
                        ? "bg-sky-500 text-white shadow-sm"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {lvl === "Clean" ? "Clean (Noiseless)" : lvl}
                  </a>
                ))}
              </div>
            </div>

            {/* Comparison Image Panel */}
            {caseManifest.noise_scenarios[selectedNoise] && (
              <div className="space-y-6">
                <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 p-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={caseManifest.noise_scenarios[selectedNoise].comparison_image_url}
                    alt={`${selectedCaseTag} 6-Method comparison under ${selectedNoise} noise`}
                    className="w-full h-auto rounded-lg shadow-lg"
                  />
                </div>

                {/* Per-Method Performance Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase bg-slate-950/50">
                        <th className="py-3 px-3">Method</th>
                        <th className="py-3 px-3 text-center">Status</th>
                        <th className="py-3 px-3 text-right">IoU</th>
                        <th className="py-3 px-3 text-right">Dice (F1)</th>
                        <th className="py-3 px-3 text-right">Precision</th>
                        <th className="py-3 px-3 text-right">Recall</th>
                        <th className="py-3 px-3 text-right">CNR</th>
                        <th className="py-3 px-3 text-right">Loc Error</th>
                        <th className="py-3 px-3 text-right">Diameter Err</th>
                        <th className="py-3 px-3 text-right">Runtime</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      {caseManifest.noise_scenarios[selectedNoise].metrics.map((m) => {
                        const isPCT = m.method_name === "PCT";
                        return (
                          <tr
                            key={m.method_name}
                            className={`hover:bg-slate-800/40 transition-colors ${
                              isPCT ? "bg-emerald-950/20 font-semibold" : ""
                            }`}
                          >
                            <td className="py-3 px-3 font-sans font-medium text-slate-200 flex items-center gap-2">
                              <span>{m.method_name}</span>
                              {isPCT && (
                                <span className="px-1.5 py-0.5 text-[9px] rounded bg-emerald-500/20 text-emerald-300 font-mono">
                                  Top
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center">
                              {caseManifest.is_healthy ? (
                                m.is_false_positive ? (
                                  <span className="inline-flex items-center gap-1 text-red-400">
                                    <XCircle className="w-3.5 h-3.5" /> FP
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 text-emerald-400">
                                    <ShieldCheck className="w-3.5 h-3.5" /> Clean
                                  </span>
                                )
                              ) : m.is_detected ? (
                                <span className="inline-flex items-center gap-1 text-emerald-400">
                                  <CheckCircle2 className="w-3.5 h-3.5" /> Detected
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-slate-400">
                                  <XCircle className="w-3.5 h-3.5" /> Undetected
                                </span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-right text-slate-300">{formatMetric(m.iou, 3)}</td>
                            <td className="py-3 px-3 text-right text-slate-300">{formatMetric(m.dice, 3)}</td>
                            <td className="py-3 px-3 text-right text-slate-300">{formatPct(m.precision)}</td>
                            <td className="py-3 px-3 text-right text-slate-300">{formatPct(m.recall)}</td>
                            <td className="py-3 px-3 text-right text-sky-400">{formatMetric(m.cnr, 2)}</td>
                            <td className="py-3 px-3 text-right text-amber-400">
                              {m.is_detected ? formatMetric(m.localization_error_detected_mm, 2, "mm") : "N/A"}
                            </td>
                            <td className="py-3 px-3 text-right text-slate-300">
                              {m.is_detected ? formatMetric(m.diameter_error_mm, 2, "mm") : "N/A"}
                            </td>
                            <td className="py-3 px-3 text-right text-slate-400">
                              {formatMetric((m.runtime_s ?? 0) * 1000, 1, "ms")}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          Case metadata not found. Please select a valid specimen from the selector above.
        </div>
      )}
    </div>
  );
}
