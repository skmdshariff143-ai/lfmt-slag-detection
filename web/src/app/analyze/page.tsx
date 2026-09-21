"use client";

import React, { useState, useRef } from "react";
import {
  UploadCloud,
  FileCode,
  Sparkles,
  Layers,
  Cpu,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Download,
  Info,
  Activity,
  Maximize2,
  Crosshair,
  Compass,
  Zap,
  BarChart2
} from "lucide-react";

interface MethodApplicability {
  method_id: string;
  display_name: string;
  is_applicable: boolean;
  status: string;
  reason: string;
  scientific_principle: string;
  required_inputs: string[];
  expected_output: string;
}

interface DefectInstance {
  defect_id: string;
  defect_type: string;
  centroid_px: [number, number];
  centroid_mm: [number, number] | null;
  bounding_box_px: [number, number, number, number];
  estimated_depth_mm: number | null;
  depth_uncertainty_range_mm: [number, number] | null;
  estimated_diameter_mm: number | null;
  area_mm2: number | null;
  area_px: number;
  confidence_score: number;
  notes: string;
}

interface AnalysisResultData {
  analysis_id: string;
  timestamp_utc: string;
  input_summary: {
    input_type: string;
    data_representation: string;
    dimensions: number[];
    n_frames: number;
    frame_rate_hz: number | null;
    fov_mm: [number, number] | null;
    raw_units: string;
    target_units: string;
    quality_status: string;
    quality_warnings: string[];
    excitation_type: string;
  };
  applicability_matrix: {
    methods: Record<string, MethodApplicability>;
    eligible_count: number;
    total_methods: number;
  };
  consensus_verdict: {
    is_anomaly_detected: boolean;
    likely_defect_type: string;
    consensus_confidence: number;
    method_agreement_ratio: number;
    agreement_level: string;
    supporting_evidence: string[];
    counter_evidence: string[];
    per_method_contributions: Record<string, { detected: boolean; confidence: number; weight: number; notes: string }>;
    final_recommendation: string;
  };
  defects: DefectInstance[];
  total_defects_found: number;
  processing_results_summary: Record<string, any>;
  physics_context: {
    material_name: string;
    thermal_diffusivity_m2_s: string;
    thermal_effusivity_w_s12_m2k: number;
    diffusion_depth_f0_mm: number | null;
    diffusion_depth_f1_mm: number | null;
    theoretical_penetration_range_mm: [number, number] | null;
  };
  ood_status: {
    status: string;
    energy_score: number;
    is_trusted_for_ai: boolean;
    notes: string;
  };
  uncertainty_estimate?: {
    epistemic_variance: number;
    entropy: number;
    is_high_confidence: boolean;
  };
  provenance_guardrails: {
    category_a: string;
    category_b: string;
    category_c: string;
    warning: string;
  };
  report_download_url?: string;
}

export default function AnalyzePage() {
  const [loading, setLoading] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisResultData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<"consensus" | "methods" | "physics" | "defects">("consensus");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const presets = [
    {
      id: "synthetic_lfmt_slag",
      title: "Numerical LFMT Slag Benchmark",
      badge: "Category A",
      desc: "3D FEM mild steel plate with subsurface slag inclusion under 0.05-0.5 Hz LFMT chirp excitation.",
      color: "border-cyan-500/40 bg-cyan-950/20 hover:bg-cyan-900/30"
    },
    {
      id: "polyu_pulsed_fbh",
      title: "PolyU Pulsed Transfer Example",
      badge: "Category B",
      desc: "Measured 150x150x10 mm mild steel plate with 11 flat-bottom holes under optical flash pulse.",
      color: "border-amber-500/40 bg-amber-950/20 hover:bg-amber-900/30"
    },
    {
      id: "single_thermal_frame",
      title: "Single Spatial Thermogram",
      badge: "2D Frame",
      desc: "Static single thermal image testing spatial contrast, gradient magnitude, and Otsu isolation.",
      color: "border-purple-500/40 bg-purple-950/20 hover:bg-purple-900/30"
    },
    {
      id: "healthy_plate",
      title: "Sound Homogeneous Specimen",
      badge: "Negative Control",
      desc: "Healthy mild steel plate with zero inclusions demonstrating false-positive rejection.",
      color: "border-emerald-500/40 bg-emerald-950/20 hover:bg-emerald-900/30"
    }
  ];

  const handleRunPreset = async (presetId: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const response = await fetch(`/api/v1/analyze/preset/${presetId}`, {
        method: "POST"
      });
      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}: ${await response.text()}`);
      }
      const data = await response.json();
      setAnalysisData(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute preset analysis.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/v1/analyze/upload", {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}: ${await response.text()}`);
      }
      const data = await response.json();
      setAnalysisData(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze uploaded file.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-10 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-8 mb-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> Research V3 Autonomous Platform
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-purple-500/10 text-purple-400 border border-purple-500/30">
                Hybrid AI + Physical Fused Engine
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Intelligent Thermographic Defect Analyzer
            </h1>
            <p className="mt-2 text-slate-400 text-sm sm:text-base max-w-3xl">
              Universal thermal data ingestion, autonomous method selection, physics-grounded signal processing (Raw Contrast, Matched Filter, PCT, SPCT, RPT), and multi-task uncertainty-aware deep learning diagnosis.
            </p>
          </div>
        </div>

        {/* Guardrail Disclaimer Banner */}
        <div className="mt-6 p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-start gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
            <div>
              <strong className="text-cyan-300 font-mono">Category A:</strong> LFMT Slag Inclusions evaluated via 3D FEM numerical simulation benchmarks.
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 mt-1.5 shrink-0" />
            <div>
              <strong className="text-amber-300 font-mono">Category B:</strong> PolyU measured pulsed flash data for transfer testing (non-LFMT, optical pulse).
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="w-2 h-2 rounded-full bg-slate-500 mt-1.5 shrink-0" />
            <div>
              <strong className="text-slate-400 font-mono">Category C:</strong> Experimental physical LFMT slag validation is future work.
            </div>
          </div>
        </div>
      </div>

      {/* Input Section: Presets & Upload */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-10">
        {/* Upload Box */}
        <div className="lg:col-span-5 flex flex-col">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-cyan-400" /> Upload Any Thermography File
          </h2>
          <div
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 border-2 border-dashed border-slate-700 hover:border-cyan-500/60 rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-slate-900/40 hover:bg-cyan-950/10 min-h-[220px]"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              className="hidden"
              accept=".zip,.npz,.npy,.mat,.csv,.png,.jpg,.jpeg,.tiff,.tif"
            />
            <div className="w-12 h-12 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 mb-3">
              <UploadCloud className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-white mb-1">Click or drag & drop thermal data</p>
            <p className="text-xs text-slate-400 max-w-xs mb-3">
              Supports ZIP sequences, CSV frames, MATLAB MAT, NPY/NPZ tensors, TIFF stacks, or PNG/JPG thermograms.
            </p>
            <div className="flex flex-wrap justify-center gap-1 text-[10px] font-mono text-slate-500">
              <span className="px-1.5 py-0.5 bg-slate-800 rounded">.ZIP</span>
              <span className="px-1.5 py-0.5 bg-slate-800 rounded">.NPZ</span>
              <span className="px-1.5 py-0.5 bg-slate-800 rounded">.NPY</span>
              <span className="px-1.5 py-0.5 bg-slate-800 rounded">.MAT</span>
              <span className="px-1.5 py-0.5 bg-slate-800 rounded">.CSV</span>
              <span className="px-1.5 py-0.5 bg-slate-800 rounded">.TIFF</span>
            </div>
          </div>
        </div>

        {/* Instant Presets */}
        <div className="lg:col-span-7 flex flex-col">
          <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" /> Instant Demonstration Presets
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 flex-1">
            {presets.map((p) => (
              <button
                key={p.id}
                onClick={() => handleRunPreset(p.id)}
                disabled={loading}
                className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${p.color} ${
                  loading ? "opacity-50 cursor-not-allowed" : "hover:scale-[1.01]"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="text-sm font-bold text-white tracking-tight">{p.title}</span>
                    <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-900/80 border border-slate-700 text-slate-300">
                      {p.badge}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-2">{p.desc}</p>
                </div>
                <div className="mt-3 text-[11px] font-medium text-cyan-400 flex items-center gap-1">
                  Run Diagnostic Pipeline →
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="p-12 rounded-2xl bg-slate-900/80 border border-slate-800 text-center my-8">
          <div className="inline-block animate-spin w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full mb-4" />
          <h3 className="text-lg font-semibold text-white">Running Autonomous Thermal Diagnostic Pipeline...</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Inspecting data representation, evaluating physical constraints, computing SVD/Matched Filter modes, and executing MC Dropout uncertainty inference.
          </p>
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/50 text-red-300 text-sm flex items-start gap-3 my-6">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Analysis Execution Error</div>
            <div className="text-xs text-red-400 mt-0.5">{errorMsg}</div>
          </div>
        </div>
      )}

      {/* Main Analysis Results Display */}
      {analysisData && !loading && (
        <div className="space-y-8 animate-fadeIn">
          {/* Top Verdict Banner */}
          <div className={`p-6 rounded-2xl border ${
            analysisData.consensus_verdict.is_anomaly_detected
              ? "bg-gradient-to-r from-red-950/30 via-slate-900 to-slate-900 border-red-500/40"
              : "bg-gradient-to-r from-emerald-950/30 via-slate-900 to-slate-900 border-emerald-500/40"
          }`}>
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold flex items-center gap-1.5 ${
                    analysisData.consensus_verdict.is_anomaly_detected
                      ? "bg-red-500/20 text-red-300 border border-red-500/40"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  }`}>
                    {analysisData.consensus_verdict.is_anomaly_detected ? (
                      <>
                        <AlertTriangle className="w-4 h-4" /> ANOMALY DETECTED
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-4 h-4" /> HEALTHY SPECIMEN (NO DEFECT)
                      </>
                    )}
                  </span>

                  <span className="px-2.5 py-1 rounded-md text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
                    ID: {analysisData.analysis_id}
                  </span>

                  <span className={`px-2.5 py-1 rounded-md text-xs font-mono ${
                    analysisData.ood_status.status === "IN_DISTRIBUTION"
                      ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
                      : "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                  }`}>
                    OOD: {analysisData.ood_status.status}
                  </span>
                </div>

                <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  {analysisData.consensus_verdict.likely_defect_type.replace(/_/g, " ")}
                </h2>
                <p className="text-sm text-slate-300 max-w-3xl">
                  {analysisData.consensus_verdict.final_recommendation}
                </p>
              </div>

              {/* Confidence & Agreement Gauges */}
              <div className="flex items-center gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
                <div className="text-center">
                  <div className="text-xs text-slate-400 font-mono mb-1">Consensus Conf</div>
                  <div className="text-2xl font-extrabold text-cyan-400 font-mono">
                    {(analysisData.consensus_verdict.consensus_confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="w-px h-10 bg-slate-800" />
                <div className="text-center">
                  <div className="text-xs text-slate-400 font-mono mb-1">Method Agreement</div>
                  <div className="text-2xl font-extrabold text-purple-400 font-mono">
                    {(analysisData.consensus_verdict.method_agreement_ratio * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">
                    {analysisData.consensus_verdict.agreement_level}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Scientific Method Applicability Matrix */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Compass className="w-4 h-4 text-cyan-400" /> Autonomous Scientific Method Applicability Matrix
              </h3>
              <span className="text-xs font-mono text-slate-400">
                {analysisData.applicability_matrix.eligible_count} / {analysisData.applicability_matrix.total_methods} Methods Active
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(analysisData.applicability_matrix.methods).map(([key, m]) => (
                <div
                  key={key}
                  className={`p-3 rounded-xl border transition-all ${
                    m.is_applicable
                      ? "bg-slate-900 border-cyan-500/30 text-slate-200"
                      : "bg-slate-950/40 border-slate-800 text-slate-500 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span className="text-xs font-bold truncate">{m.display_name}</span>
                    <span className={`px-1.5 py-0.5 text-[9px] font-mono rounded ${
                      m.is_applicable ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-800 text-slate-500"
                    }`}>
                      {m.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2 mb-2">{m.reason}</p>
                  <div className="text-[10px] font-mono text-slate-500 truncate">
                    Inputs: {m.required_inputs.join(", ")}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            {[
              { id: "consensus", label: "Multi-Method Fusion & Evidence", icon: ShieldCheck },
              { id: "defects", label: `Isolated Defects (${analysisData.total_defects_found})`, icon: Crosshair },
              { id: "methods", label: "Algorithm Outputs", icon: Layers },
              { id: "physics", label: "Thermodynamics & Diffusion", icon: BarChart2 }
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id as any)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                    selectedTab === tab.id
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab 1: Consensus & Evidence */}
          {selectedTab === "consensus" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Supporting Evidence */}
              <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
                <h4 className="text-sm font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" /> Supporting Diagnostic Evidence
                </h4>
                {analysisData.consensus_verdict.supporting_evidence.length > 0 ? (
                  <ul className="space-y-2 text-xs text-slate-300">
                    {analysisData.consensus_verdict.supporting_evidence.map((ev, i) => (
                      <li key={i} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500">No positive defect evidence identified.</p>
                )}
              </div>

              {/* Counter Evidence / Sound Indications */}
              <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800">
                <h4 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
                  <Info className="w-4 h-4" /> Sound Background & Negative Evidence
                </h4>
                {analysisData.consensus_verdict.counter_evidence.length > 0 ? (
                  <ul className="space-y-2 text-xs text-slate-400">
                    {analysisData.consensus_verdict.counter_evidence.map((ev, i) => (
                      <li key={i} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-600 mt-1.5 shrink-0" />
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-slate-500">All evaluated methods indicated anomalies.</p>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Defects Table */}
          {selectedTab === "defects" && (
            <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
              <h4 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <Crosshair className="w-4 h-4 text-cyan-400" /> Sizing and Spatial Localization Results
              </h4>
              {analysisData.defects.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="p-3">Defect ID</th>
                        <th className="p-3">Classification</th>
                        <th className="p-3">Centroid (x, y mm)</th>
                        <th className="p-3">Diameter (mm)</th>
                        <th className="p-3">Estimated Depth (mm)</th>
                        <th className="p-3">Area (mm²)</th>
                        <th className="p-3">Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-200">
                      {analysisData.defects.map((d) => (
                        <tr key={d.defect_id} className="hover:bg-slate-800/40">
                          <td className="p-3 font-bold text-cyan-400">{d.defect_id}</td>
                          <td className="p-3">{d.defect_type}</td>
                          <td className="p-3">
                            {d.centroid_mm ? `(${d.centroid_mm[0].toFixed(1)}, ${d.centroid_mm[1].toFixed(1)})` : "N/A"}
                          </td>
                          <td className="p-3">{d.estimated_diameter_mm ? `${d.estimated_diameter_mm.toFixed(1)} mm` : "N/A"}</td>
                          <td className="p-3">
                            {d.estimated_depth_mm ? (
                              <span>
                                {d.estimated_depth_mm.toFixed(2)} mm{" "}
                                {d.depth_uncertainty_range_mm && (
                                  <span className="text-[10px] text-slate-500">
                                    [{d.depth_uncertainty_range_mm[0].toFixed(2)} - {d.depth_uncertainty_range_mm[1].toFixed(2)}]
                                  </span>
                                )}
                              </span>
                            ) : "N/A"}
                          </td>
                          <td className="p-3">{d.area_mm2 ? `${d.area_mm2.toFixed(1)} mm²` : `${d.area_px} px`}</td>
                          <td className="p-3">{(d.confidence_score * 100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-slate-500">No defect candidates segmented.</p>
              )}
            </div>
          )}

          {/* Tab 3: Algorithm Outputs */}
          {selectedTab === "methods" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(analysisData.processing_results_summary).map(([methodKey, res]) => (
                <div key={methodKey} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-bold text-cyan-400 uppercase">{methodKey.replace(/_/g, " ")}</span>
                    <span className={`px-2 py-0.5 text-[10px] font-mono rounded ${
                      res.is_detected ? "bg-red-500/20 text-red-300" : "bg-emerald-500/20 text-emerald-300"
                    }`}>
                      {res.is_detected ? "Anomaly" : "Clean"}
                    </span>
                  </div>
                  <pre className="text-[11px] font-mono text-slate-300 bg-slate-950 p-2.5 rounded-lg overflow-x-auto">
                    {JSON.stringify(res, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}

          {/* Tab 4: Thermodynamics */}
          {selectedTab === "physics" && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800">
              <h4 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-cyan-400" /> Thermodynamic Diffusion Properties
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs font-mono">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-500 mb-1">Material</div>
                  <div className="text-sm font-bold text-white uppercase">{analysisData.physics_context.material_name}</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-500 mb-1">Thermal Diffusivity (α)</div>
                  <div className="text-sm font-bold text-cyan-400">{analysisData.physics_context.thermal_diffusivity_m2_s} m²/s</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-500 mb-1">Thermal Effusivity (e)</div>
                  <div className="text-sm font-bold text-cyan-400">{analysisData.physics_context.thermal_effusivity_w_s12_m2k} W·s½/(m²·K)</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-slate-500 mb-1">Theoretical Penetration Range</div>
                  <div className="text-sm font-bold text-white">
                    {analysisData.physics_context.theoretical_penetration_range_mm
                      ? `${analysisData.physics_context.theoretical_penetration_range_mm[0]} - ${analysisData.physics_context.theoretical_penetration_range_mm[1]} mm`
                      : "N/A"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Export Downloads */}
          <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
            <div className="text-xs text-slate-400">
              Analysis completed in accordance with Research V3 strict reproducibility standards.
            </div>
            <div className="flex items-center gap-2">
              <a
                href={`/api/v1/analyze/${analysisData.analysis_id}/report`}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/30 flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" /> Download Full JSON Report
              </a>
              <a
                href={`/api/v1/analyze/${analysisData.analysis_id}/figure`}
                target="_blank"
                rel="noreferrer"
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-200 border border-slate-700 hover:bg-slate-700 flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" /> Download 300 DPI Diagnostic Panel
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
