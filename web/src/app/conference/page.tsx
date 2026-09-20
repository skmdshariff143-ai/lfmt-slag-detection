"use client";
import React, { useState, useEffect } from "react";
import Image from "next/image";
import {
  Maximize,
  Minimize,
  Eye,
  Sliders,
  Sparkles,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import { CaseManifest, CaseIndexItem } from "@/types/research";
import { formatMetric, formatPct, METHOD_COLORS } from "@/lib/data";

const DIAMETERS = [4.0, 6.0, 8.0, 10.0, 12.0, 0.0];
const DEPTHS = [0.2, 0.4, 0.6, 0.8, 1.0];
const NOISE_OPTIONS = ["Clean", "30dB", "25dB", "20dB"];

export default function ConferencePage() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedDiam, setSelectedDiam] = useState<number>(8.0);
  const [selectedDepth, setSelectedDepth] = useState<number>(0.4);
  const [selectedNoise, setSelectedNoise] = useState<string>("30dB");
  const [caseManifest, setCaseManifest] = useState<CaseManifest | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Compute tag from selected parameters
  const currentTag =
    selectedDiam === 0.0
      ? "HEALTHY_CONTROL"
      : `D${Math.round(selectedDiam * 10).toString().padStart(3, "0")}_Z${Math.round(
          selectedDepth * 10
        )
          .toString()
          .padStart(3, "0")}`;

  // Fetch case manifest
  useEffect(() => {
    async function loadCase() {
      setLoading(true);
      try {
        const res = await fetch(`/cases/${currentTag}.json`);
        if (res.ok) {
          const data = await res.json();
          setCaseManifest(data);
        } else {
          // Fallback to D080_Z004 if not available
          const fbRes = await fetch(`/cases/D080_Z004.json`);
          if (fbRes.ok) {
            const fbData = await fbRes.json();
            setCaseManifest(fbData);
          }
        }
      } catch (err) {
        console.error("Failed to load case data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCase();
  }, [currentTag]);

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.error("Error attempting to enable fullscreen:", err);
      });
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
        setIsFullscreen(false);
      }
    }
  };

  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFsChange);
    return () => document.removeEventListener("fullscreenchange", handleFsChange);
  }, []);

  const noiseData = caseManifest?.noise_scenarios?.[selectedNoise];
  const comparisonImageUrl = noiseData?.comparison_image_url || `/thermograms/D080_Z004/comparison_${selectedNoise.toLowerCase()}.png`;
  const metrics = noiseData?.metrics || [];

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-100 ${isFullscreen ? "p-4" : "py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto"} space-y-5`}>
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-900/80 backdrop-blur-md">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              CONFERENCE PRESENTATION MODE
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Simulation-Based Numerical Benchmark
            </span>
          </div>
          <h1 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
            LFMT Subsurface Slag Defect Detection
          </h1>
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono pt-0.5">
            <span>Solver: <strong className="text-slate-200">3-D FEM (`scikit-fem`)</strong></span>
            <span>•</span>
            <span>Matrix: <strong className="text-slate-200">Mild Steel (AISI 1018)</strong></span>
            <span>•</span>
            <span>Inclusion: <strong className="text-slate-200">Silicate Slag</strong></span>
            <span>•</span>
            <span>Dataset: <strong className="text-cyan-400">4,030 Evaluations</strong></span>
          </div>
        </div>

        <button
          onClick={toggleFullscreen}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors"
        >
          {isFullscreen ? <Minimize className="w-4 h-4 text-amber-400" /> : <Maximize className="w-4 h-4 text-cyan-400" />}
          {isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
        </button>
      </div>

      {/* Interactive Controls Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl border border-slate-800 bg-slate-900/60 font-mono text-xs">
        {/* Diameter Selector */}
        <div className="space-y-2">
          <label className="text-slate-400 uppercase text-[11px] tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            Defect Diameter D [mm]
          </label>
          <div className="flex flex-wrap gap-1.5">
            {DIAMETERS.map((d) => (
              <button
                key={d}
                onClick={() => setSelectedDiam(d)}
                className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors border ${
                  selectedDiam === d
                    ? "bg-cyan-500 text-slate-950 border-cyan-400 font-bold"
                    : "bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800"
                }`}
              >
                {d === 0.0 ? "Healthy (0mm)" : `${d.toFixed(1)} mm`}
              </button>
            ))}
          </div>
        </div>

        {/* Depth Selector */}
        <div className="space-y-2">
          <label className="text-slate-400 uppercase text-[11px] tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            Subsurface Depth z [mm]
          </label>
          <div className="flex flex-wrap gap-1.5">
            {DEPTHS.map((z) => (
              <button
                key={z}
                disabled={selectedDiam === 0.0}
                onClick={() => setSelectedDepth(z)}
                className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors border ${
                  selectedDiam === 0.0
                    ? "opacity-30 cursor-not-allowed bg-slate-900 border-slate-800 text-slate-600"
                    : selectedDepth === z
                    ? "bg-indigo-500 text-white border-indigo-400 font-bold"
                    : "bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800"
                }`}
              >
                {z.toFixed(1)} mm
              </button>
            ))}
          </div>
        </div>

        {/* Noise Condition Selector */}
        <div className="space-y-2">
          <label className="text-slate-400 uppercase text-[11px] tracking-wider flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            Sensor Noise Condition
          </label>
          <div className="flex flex-wrap gap-1.5">
            {NOISE_OPTIONS.map((nc) => (
              <button
                key={nc}
                onClick={() => setSelectedNoise(nc)}
                className={`px-3 py-1.5 rounded-md font-medium text-xs transition-colors border ${
                  selectedNoise === nc
                    ? "bg-emerald-500 text-slate-950 border-emerald-400 font-bold"
                    : "bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800"
                }`}
              >
                {nc === "Clean" ? "Clean (0 dB)" : `AWGN ${nc}`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Visual: 6-Panel Multi-Algorithm Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7 rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-semibold text-white uppercase font-mono">
                Multi-Method Contrast Maps ({currentTag}, {selectedNoise})
              </span>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Strict Blind Spatial Isolation
            </span>
          </div>

          <div className="relative aspect-[9/5.5] w-full rounded-lg overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={comparisonImageUrl}
              alt={`LFMT Multi-Method Comparison for ${currentTag}`}
              className="w-full h-full object-contain"
            />
          </div>

          <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-400 text-center">
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800">
              Top Left: Ground Truth
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800">
              Top Mid: Raw Contrast
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800">
              Top Right: Matched Filter
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800">
              Bot Left: PCT (EOF Mode)
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800">
              Bot Mid: SPCT (Sparse PCA)
            </div>
            <div className="p-1.5 rounded bg-slate-950 border border-slate-800">
              Bot Right: RPT (Random Proj)
            </div>
          </div>
        </div>

        {/* Quantitative Metrics Table for Case */}
        <div className="lg:col-span-5 rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3 flex flex-col justify-between">
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-semibold text-white uppercase font-mono">
                Quantitative Case Evaluation
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                {selectedDiam > 0 ? `D=${selectedDiam.toFixed(1)}mm, z=${selectedDepth.toFixed(1)}mm` : "Healthy Control Plate"}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left text-slate-300 font-mono">
                <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="px-2 py-2">Method</th>
                    <th className="px-2 py-2 text-center">Detected</th>
                    <th className="px-2 py-2 text-right">CNR</th>
                    <th className="px-2 py-2 text-right">IoU</th>
                    <th className="px-2 py-2 text-right">E_loc [mm]</th>
                    <th className="px-2 py-2 text-right">Time [ms]</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-[11px]">
                  {metrics.map((m) => (
                    <tr key={m.method_name} className="hover:bg-slate-950/40">
                      <td className="px-2 py-2.5 font-bold text-slate-200" style={{ color: METHOD_COLORS[m.method_name] || "#fff" }}>
                        {m.method_name}
                      </td>
                      <td className="px-2 py-2.5 text-center">
                        {m.is_detected ? (
                          <span className="inline-flex items-center gap-1 text-emerald-400">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            YES
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-slate-500">
                            <AlertCircle className="w-3.5 h-3.5" />
                            NO
                          </span>
                        )}
                      </td>
                      <td className="px-2 py-2.5 text-right font-semibold">
                        {formatMetric(m.cnr, 2)}
                      </td>
                      <td className="px-2 py-2.5 text-right">
                        {formatMetric(m.iou, 3)}
                      </td>
                      <td className="px-2 py-2.5 text-right">
                        {m.is_detected ? formatMetric(m.localization_error_detected_mm, 2) : "N/A"}
                      </td>
                      <td className="px-2 py-2.5 text-right text-slate-400">
                        {formatMetric((m.runtime_seconds ?? m.runtime_s ?? 0) * 1000, 1)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
            <div className="font-semibold text-slate-300 flex items-center gap-1">
              <HelpCircle className="w-3 h-3 text-cyan-400" />
              Evaluation Criteria Note
            </div>
            <p>
              A defect is evaluated as <strong>Detected</strong> if blind isolation produces a candidate with spatial overlap (IoU &gt; 0) and centroid proximity E<sub>loc</sub> &le; max(R<sub>true</sub>, 5.0 mm). When undetected, localization error is strictly <strong>N/A</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}