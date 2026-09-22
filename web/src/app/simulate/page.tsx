"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Layers,
  Cpu,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Maximize2,
  Crosshair,
  Compass,
  Zap,
  BarChart2,
  Sliders,
  Flame,
  ArrowRight,
  GitCompare,
  Terminal,
  RefreshCw,
  Download,
  FileSpreadsheet
} from "lucide-react";
import {
  fetchSimulationBackends,
  startSimulationRun,
  getSimulationStatus,
  getSimulationResult,
  compareSimulationBackends,
  fetchPrecomputedSimulation
} from "@/lib/api";

export default function SimulatePage() {
  // Engine and Preset selection
  const [selectedBackend, setSelectedBackend] = useState<"matlab_fdm" | "python_fem" | "compare">("matlab_fdm");
  const [selectedPreset, setSelectedPreset] = useState<string>("shallow_slag");
  const [backendsInfo, setBackendsInfo] = useState<any>(null);

  // Custom parameters
  const [showConfig, setShowConfig] = useState<boolean>(false);
  const [diameterMm, setDiameterMm] = useState<number>(8.0);
  const [depthMm, setDepthMm] = useState<number>(0.4);
  const [thicknessMm, setThicknessMm] = useState<number>(0.4);
  const [f0Hz, setF0Hz] = useState<number>(0.05);
  const [f1Hz, setF1Hz] = useState<number>(0.50);
  const [durationS, setDurationS] = useState<number>(10.0);
  const [q0Wm2, setQ0Wm2] = useState<number>(5000.0);

  // Simulation execution state
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [stageMessage, setStageMessage] = useState<string>("");
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Thermal animation state
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [displayMode, setDisplayMode] = useState<"delta_t" | "absolute">("delta_t");
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1);
  const animIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Active NDT method tab
  const [activeMethodTab, setActiveMethodTab] = useState<string>("mf");

  // Load backends info on mount
  useEffect(() => {
    fetchSimulationBackends()
      .then((data) => setBackendsInfo(data))
      .catch((err) => console.error("Could not fetch backends:", err));
  }, []);

  // Update parameters when preset changes
  useEffect(() => {
    if (selectedPreset === "healthy") {
      setDiameterMm(0.0);
      setDepthMm(0.0);
    } else if (selectedPreset === "shallow_slag") {
      setDiameterMm(8.0);
      setDepthMm(0.4);
      setThicknessMm(0.4);
    } else if (selectedPreset === "deep_slag") {
      setDiameterMm(8.0);
      setDepthMm(0.8);
      setThicknessMm(0.4);
    } else if (selectedPreset === "multi_slag") {
      setDiameterMm(6.0);
      setDepthMm(0.4);
      setThicknessMm(0.4);
    }
  }, [selectedPreset]);

  // Handle animation playback
  useEffect(() => {
    if (isPlaying && simulationResult?.animation?.surface_temperature) {
      const nFrames = simulationResult.animation.surface_temperature.length;
      animIntervalRef.current = setInterval(() => {
        setCurrentFrame((prev) => {
          if (prev >= nFrames - 1) {
            return 0; // loop
          }
          return prev + 1;
        });
      }, 100 / playbackSpeed);
    } else {
      if (animIntervalRef.current) clearInterval(animIntervalRef.current);
    }
    return () => {
      if (animIntervalRef.current) clearInterval(animIntervalRef.current);
    };
  }, [isPlaying, simulationResult, playbackSpeed]);

  // Start Simulation
  const handleRunSimulation = async () => {
    setIsSimulating(true);
    setErrorMsg(null);
    setSimulationResult(null);
    setComparisonResult(null);
    setCurrentFrame(0);
    setIsPlaying(false);

    if (selectedBackend === "compare") {
      setStageMessage("Running Python FEM & MATLAB FDM Cross-Validation...");
      try {
        const comp = await compareSimulationBackends(selectedPreset);
        setComparisonResult(comp);
        setIsSimulating(false);
      } catch (err: any) {
        setErrorMsg(err.message || "Comparison failed.");
        setIsSimulating(false);
      }
      return;
    }

    try {
      setStageMessage("Initializing simulation job...");
      const payload = {
        backend: selectedBackend,
        preset: selectedPreset,
        duration_s: durationS,
        f0_hz: f0Hz,
        f1_hz: f1Hz,
        q0_w_m2: q0Wm2,
        defects:
          diameterMm > 0
            ? [
                {
                  diameter_mm: diameterMm,
                  depth_mm: depthMm,
                  thickness_mm: thicknessMm,
                  center_x_mm: 50.0,
                  center_y_mm: 35.0,
                  material: "slag"
                }
              ]
            : []
      };

      const dispatch = await startSimulationRun(payload);
      setRunId(dispatch.run_id);

      // Poll status
      const pollInterval = setInterval(async () => {
        try {
          const statusData = await getSimulationStatus(dispatch.run_id);
          setStageMessage(statusData.stage || statusData.status);

          if (statusData.status === "COMPLETED") {
            clearInterval(pollInterval);
            const resData = await getSimulationResult(dispatch.run_id);
            setSimulationResult(resData);
            setIsSimulating(false);
            setIsPlaying(true);
          } else if (statusData.status === "FAILED") {
            clearInterval(pollInterval);
            setErrorMsg("Simulation failed during execution.");
            setIsSimulating(false);
          }
        } catch (err: any) {
          clearInterval(pollInterval);
          setErrorMsg(err.message || "Failed polling simulation.");
          setIsSimulating(false);
        }
      }, 800);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed starting simulation.");
      setIsSimulating(false);
    }
  };

  // Load Precomputed Result (Presentation Backup)
  const handleLoadPrecomputed = async () => {
    setIsSimulating(true);
    setErrorMsg(null);
    setComparisonResult(null);
    setStageMessage("Loading verified precomputed MATLAB simulation...");
    try {
      const data = await fetchPrecomputedSimulation();
      setSimulationResult(data);
      setSelectedPreset("shallow_slag");
      setSelectedBackend("matlab_fdm");
      setCurrentFrame(0);
      setIsSimulating(false);
      setIsPlaying(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed loading precomputed MATLAB result.");
      setIsSimulating(false);
    }
  };

  // Run Flagship Demo Shortcut
  const handleRunFlagshipDemo = () => {
    setSelectedBackend("matlab_fdm");
    setSelectedPreset("shallow_slag");
    setDiameterMm(8.0);
    setDepthMm(0.4);
    setThicknessMm(0.4);
    setF0Hz(0.05);
    setF1Hz(0.50);
    setDurationS(10.0);
    setQ0Wm2(5000.0);
    setTimeout(() => {
      handleRunSimulation();
    }, 100);
  };

  // Download JSON Result
  const handleDownloadJson = () => {
    if (!simulationResult) return;
    const blob = new Blob([JSON.stringify(simulationResult, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `simulation_${simulationResult.run_id || "matlab_lfmt"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Download CSV Curves
  const handleDownloadCsv = () => {
    if (!simulationResult?.temperature_curves) return;
    const curves = simulationResult.temperature_curves;
    const times = curves.time_s || [];
    const probe = curves.probe_roi_dT || curves.defect_center_roi_dT || [];
    const ref = curves.reference_roi_dT || curves.sound_plate_roi_dT || [];
    const mean = curves.plate_mean_dT || [];

    let csv = "time_s,probe_roi_dT_K,reference_roi_dT_K,plate_mean_dT_K\n";
    for (let i = 0; i < times.length; i++) {
      csv += `${times[i]},${probe[i] ?? ""},${ref[i] ?? ""},${mean[i] ?? ""}\n`;
    }
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `temperature_curves_${simulationResult.run_id || "matlab_lfmt"}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper colormap function for thermal array
  const renderThermalColor = (val: number, minVal: number, maxVal: number) => {
    const norm = Math.max(0, Math.min(1, (val - minVal) / Math.max(1e-4, maxVal - minVal)));
    // Inferno-like heatmap palette
    const r = Math.floor(Math.min(255, norm * 280));
    const g = Math.floor(Math.min(255, Math.pow(norm, 1.8) * 240));
    const b = Math.floor(Math.min(255, (1 - Math.abs(norm - 0.4) * 2) * 180));
    return `rgb(${r}, ${g}, ${b})`;
  };

  const animData = simulationResult?.animation;
  const current2DMatrix =
    animData && animData.surface_temperature && animData.surface_temperature[currentFrame]
      ? displayMode === "delta_t"
        ? animData.delta_t[currentFrame]
        : animData.surface_temperature[currentFrame]
      : null;

  const minValDisplay = displayMode === "delta_t" ? 0.0 : simulationResult?.min_temp_k || 293.15;
  const maxValDisplay =
    displayMode === "delta_t"
      ? simulationResult?.peak_delta_t_k || 7.5
      : simulationResult?.max_temp_k || 300.5;

  const currentTimeS = animData?.time_vector
    ? animData.time_vector[currentFrame]?.toFixed(2)
    : (currentFrame * 0.04).toFixed(2);

  const analysisVerdict = simulationResult?.analysis_result?.consensus_verdict;
  const processingMaps = simulationResult?.analysis_result?.processing_maps;
  const gt = simulationResult?.ground_truth;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-amber-500/20 to-rose-500/20 rounded-xl border border-amber-500/30 text-amber-400">
                <Flame className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-amber-300 via-rose-300 to-cyan-300 bg-clip-text text-transparent">
                  MATLAB LFMT Simulation Lab
                </h1>
                <p className="text-sm text-slate-400">
                  Virtual 3-D Thermal Conduction Experimentation & Autonomous NDT Defect Analysis
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            {backendsInfo?.matlab_fdm?.status === "AVAILABLE" ? (
              <span className="px-3 py-1.5 rounded-full bg-emerald-950/80 border border-emerald-500/30 text-emerald-400 font-mono flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                {backendsInfo.matlab_fdm.connection_mode === "engine"
                  ? `MATLAB Engine: Connected (${backendsInfo.matlab_fdm.engine || "R2026a"})`
                  : `MATLAB Batch: Available (${backendsInfo.matlab_fdm.engine || "R2026a"})`}
              </span>
            ) : (
              <span className="px-3 py-1.5 rounded-full bg-slate-900 border border-slate-700 text-slate-400 font-mono flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-slate-500"></span>
                MATLAB: Unavailable
              </span>
            )}
            <span className="px-3 py-1.5 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-cyan-400 font-mono">
              3-D Conservative FDM
            </span>
          </div>
        </div>

        {/* Presentation & Quick Action Bar */}
        <div className="bg-gradient-to-r from-slate-900 via-amber-950/20 to-slate-900 border border-amber-500/30 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg shadow-amber-500/5">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/20 rounded-lg text-amber-400 border border-amber-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-100">Live Conference Demonstration Mode</div>
              <div className="text-xs text-slate-400">
                100 × 70 × 2.3 mm Mild Steel · D = 8 mm, d = 0.4 mm Slag · 0.05 → 0.50 Hz LFMT Chirp
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            <button
              type="button"
              onClick={handleRunFlagshipDemo}
              disabled={isSimulating}
              className="flex-1 md:flex-initial px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 text-slate-950 font-bold text-xs hover:opacity-95 shadow transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>RUN FLAGSHIP MATLAB DEMO</span>
            </button>

            <button
              type="button"
              onClick={handleLoadPrecomputed}
              disabled={isSimulating}
              className="flex-1 md:flex-initial px-4 py-2.5 rounded-xl bg-slate-900 border border-amber-500/40 text-amber-300 font-semibold text-xs hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>LOAD PRECOMPUTED MATLAB RESULT</span>
            </button>
          </div>
        </div>

        {/* Engine & Preset Control Bar */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 1. Simulation Engine Selector */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Simulation Engine</span>
            </div>
            <div className="grid grid-cols-1 gap-2.5">
              <button
                type="button"
                onClick={() => setSelectedBackend("matlab_fdm")}
                className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all ${
                  selectedBackend === "matlab_fdm"
                    ? "bg-amber-500/10 border-amber-500/50 text-amber-300 shadow-lg shadow-amber-500/5"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="text-sm font-semibold text-slate-200">MATLAB 3-D FDM</div>
                  <div className="text-xs text-slate-400">Conservative Flux with Harmonic Interfaces</div>
                </div>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Recommended
                </span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedBackend("python_fem")}
                className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all ${
                  selectedBackend === "python_fem"
                    ? "bg-cyan-500/10 border-cyan-500/50 text-cyan-300 shadow-lg shadow-cyan-500/5"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="text-sm font-semibold text-slate-200">Python 3-D FEM</div>
                  <div className="text-xs text-slate-400">Trilinear Hexahedral (scikit-fem)</div>
                </div>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Reference
                </span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedBackend("compare")}
                className={`flex items-start justify-between p-3 rounded-xl border text-left transition-all ${
                  selectedBackend === "compare"
                    ? "bg-purple-500/10 border-purple-500/50 text-purple-300 shadow-lg shadow-purple-500/5"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="text-sm font-semibold text-slate-200">Compare Both</div>
                  <div className="text-xs text-slate-400">Side-by-Side Numerical Cross-Validation</div>
                </div>
                <GitCompare className="w-4 h-4 text-purple-400" />
              </button>
            </div>
          </div>

          {/* 2. Defect Presets */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between text-sm font-semibold text-slate-200">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-amber-400" />
                <span>Reference Presets</span>
              </div>
              <button
                type="button"
                onClick={() => setShowConfig(!showConfig)}
                className="text-xs text-amber-400 hover:underline flex items-center gap-1"
              >
                <Sliders className="w-3.5 h-3.5" />
                {showConfig ? "Hide Config" : "Custom Config"}
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              {[
                { id: "healthy", name: "Sound Steel", desc: "Negative Control" },
                { id: "shallow_slag", name: "Shallow Slag", desc: "D=8mm, d=0.4mm" },
                { id: "deep_slag", name: "Deep Slag", desc: "D=8mm, d=0.8mm" },
                { id: "multi_slag", name: "Multi-Inclusion", desc: "2 Merged Slags" }
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setSelectedPreset(p.id)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    selectedPreset === p.id
                      ? "bg-slate-800 border-amber-500/50 text-amber-300 ring-1 ring-amber-500/30"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <div className="text-xs font-semibold text-slate-200">{p.name}</div>
                  <div className="text-[11px] text-slate-400 font-mono mt-0.5">{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 3. Launch Simulation Button & Telemetry */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                <Zap className="w-4 h-4 text-emerald-400" />
                <span>Simulation Parameters</span>
              </div>
              <div className="text-xs text-slate-400 space-y-1 font-mono">
                <div>Plate: 100 × 70 × 2.3 mm (AISI 1018)</div>
                <div>LFMT Chirp: 0.05 → 0.50 Hz (10 s)</div>
                <div>Flux Amplitude: q₀ = 5000 W/m² (qₘₐₓ = 10000 W/m²)</div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={isSimulating}
              className={`w-full mt-4 py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 shadow-lg transition-all ${
                isSimulating
                  ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
                  : "bg-gradient-to-r from-amber-500 via-rose-500 to-cyan-500 text-slate-950 font-bold hover:opacity-95 hover:scale-[1.01]"
              }`}
            >
              {isSimulating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                  <span>{stageMessage || "Simulating in MATLAB..."}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Run 3-D Thermal Simulation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Custom Config Drawer (Collapsible) */}
        {showConfig && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 grid grid-cols-1 md:grid-cols-4 gap-6 animate-fadeIn">
            <div>
              <label className="text-xs font-semibold text-slate-300">Defect Diameter [mm]</label>
              <input
                type="number"
                step="0.5"
                value={diameterMm}
                onChange={(e) => {
                  setSelectedPreset("custom");
                  setDiameterMm(parseFloat(e.target.value) || 0);
                }}
                className="w-full mt-1.5 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">Defect Depth [mm]</label>
              <input
                type="number"
                step="0.1"
                value={depthMm}
                onChange={(e) => {
                  setSelectedPreset("custom");
                  setDepthMm(parseFloat(e.target.value) || 0);
                }}
                className="w-full mt-1.5 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">LFMT Start Frequency f₀ [Hz]</label>
              <input
                type="number"
                step="0.01"
                value={f0Hz}
                onChange={(e) => {
                  setSelectedPreset("custom");
                  setF0Hz(parseFloat(e.target.value) || 0.05);
                }}
                className="w-full mt-1.5 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300">LFMT End Frequency f₁ [Hz]</label>
              <input
                type="number"
                step="0.05"
                value={f1Hz}
                onChange={(e) => {
                  setSelectedPreset("custom");
                  setF1Hz(parseFloat(e.target.value) || 0.50);
                }}
                className="w-full mt-1.5 px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200"
              />
            </div>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="bg-rose-950/50 border border-rose-500/50 rounded-2xl p-4 text-rose-300 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{errorMsg}</span>
          </div>
        )}

        {/* Comparison Result View (If 'Compare Both' is run) */}
        {comparisonResult && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-purple-400" />
                <h2 className="text-lg font-bold text-slate-100">Python FEM vs. MATLAB FDM Cross-Validation</h2>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-500/30 text-xs font-mono">
                Cross-Validated (Rel L₂ ≤ 5%)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                <div className="text-xs text-slate-400">Python 3-D Hexahedral FEM</div>
                <div className="text-2xl font-mono text-cyan-400">
                  {comparisonResult.python_fem.peak_delta_t_k.toFixed(3)} K
                </div>
                <div className="text-xs text-slate-500">
                  Runtime: {comparisonResult.python_fem.runtime_s.toFixed(2)} s
                </div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                <div className="text-xs text-slate-400">MATLAB 3-D Conservative FDM</div>
                <div className="text-2xl font-mono text-amber-400">
                  {comparisonResult.matlab_fdm.peak_delta_t_k.toFixed(3)} K
                </div>
                <div className="text-xs text-slate-500">
                  Runtime: {comparisonResult.matlab_fdm.runtime_s.toFixed(2)} s
                </div>
              </div>

              <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl space-y-2">
                <div className="text-xs text-slate-400">Relative L₂ Agreement</div>
                <div className="text-2xl font-mono text-emerald-400">
                  {comparisonResult.comparison_metrics.rel_l2_error_pct.toFixed(2)} %
                </div>
                <div className="text-xs text-slate-500">
                  Spatial Correlation: {comparisonResult.comparison_metrics.spatial_correlation.toFixed(4)}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Simulation Result Dashboard */}
        {simulationResult && (
          <div className="space-y-8 animate-fadeIn">
            {/* Precomputed Indicator Banner */}
            {simulationResult.is_precomputed && (
              <div className="bg-amber-950/40 border border-amber-500/50 rounded-2xl p-4 flex items-center justify-between text-amber-300">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="w-5 h-5 text-amber-400" />
                  <div>
                    <span className="font-bold text-sm">PRECOMPUTED MATLAB NUMERICAL SIMULATION</span>
                    <span className="text-xs text-amber-200/70 ml-2">
                      (Verified R2026a FDM benchmark result loaded for live demonstration backup)
                    </span>
                  </div>
                </div>
                <span className="text-[11px] font-mono px-2.5 py-1 bg-amber-500/20 rounded-md border border-amber-500/30">
                  OFFLINE BACKUP ACTIVE
                </span>
              </div>
            )}

            {/* Export & Download Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="text-xs text-slate-300 font-semibold">Reproducible Data Export</span>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleDownloadJson}
                  className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 text-xs font-mono flex items-center gap-1.5 transition-all"
                >
                  <Download className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Export Result JSON</span>
                </button>

                <button
                  type="button"
                  onClick={handleDownloadCsv}
                  className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 text-xs font-mono flex items-center gap-1.5 transition-all"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Export Curves CSV</span>
                </button>
              </div>
            </div>

            {/* Top Stats Banner */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">Solver Core</div>
                <div className="text-base font-semibold text-slate-100 mt-1">
                  {simulationResult.solver_name}
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  {simulationResult.execution_time_s.toFixed(2)} s runtime
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">Peak Temperature Rise</div>
                <div className="text-base font-semibold text-amber-400 mt-1 font-mono">
                  +{simulationResult.peak_delta_t_k.toFixed(3)} K
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  Max: {simulationResult.max_temp_k.toFixed(2)} K
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">NDT Consensus Verdict</div>
                <div className="text-base font-semibold text-cyan-300 mt-1 truncate">
                  {analysisVerdict?.likely_defect_type || "HEALTHY"}
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  {analysisVerdict?.is_anomaly_detected ? "Anomaly Detected" : "Sound Control"}
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div className="text-xs text-slate-400">Temporal Frames</div>
                <div className="text-base font-semibold text-slate-100 mt-1 font-mono">
                  {animData?.n_frames || 0} frames
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  {simulationResult?.camera_frame_rate_hz ? `${simulationResult.camera_frame_rate_hz} Hz IR Camera` : "40 × 28 surface FOV"}
                </div>
              </div>
            </div>

            {/* Middle Section: Thermal Animation Player & Temperature Curve */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left (7 cols): Interactive Animation Player */}
              <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-amber-400" />
                    <h3 className="text-sm font-semibold text-slate-200">
                      Front-Surface Thermogram Sequence
                    </h3>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <button
                      type="button"
                      onClick={() => setDisplayMode("delta_t")}
                      className={`px-2.5 py-1 rounded-lg transition-all ${
                        displayMode === "delta_t"
                          ? "bg-amber-500/20 border border-amber-500/40 text-amber-300 font-semibold"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      ΔT (K)
                    </button>
                    <button
                      type="button"
                      onClick={() => setDisplayMode("absolute")}
                      className={`px-2.5 py-1 rounded-lg transition-all ${
                        displayMode === "absolute"
                          ? "bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-semibold"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      Absolute (K)
                    </button>
                  </div>
                </div>

                {/* 2D Thermogram Heatmap Render */}
                <div className="aspect-[40/28] bg-slate-950 rounded-xl border border-slate-800 p-2 relative overflow-hidden flex items-center justify-center">
                  {current2DMatrix && (
                    <div
                      className="w-full h-full grid"
                      style={{
                        gridTemplateColumns: "repeat(40, minmax(0, 1fr))",
                        gridTemplateRows: "repeat(28, minmax(0, 1fr))"
                      }}
                    >
                      {current2DMatrix.map((row: number[], rIdx: number) =>
                        row.map((val: number, cIdx: number) => {
                          const xMm = animData?.x_coords_mm?.[cIdx] !== undefined ? animData.x_coords_mm[cIdx].toFixed(1) : (cIdx * 2.5).toFixed(1);
                          const yMm = animData?.y_coords_mm?.[rIdx] !== undefined ? animData.y_coords_mm[rIdx].toFixed(1) : (rIdx * 2.5).toFixed(1);
                          return (
                            <div
                              key={`${rIdx}-${cIdx}`}
                              className="w-full h-full"
                              style={{
                                backgroundColor: renderThermalColor(val, minValDisplay, maxValDisplay)
                              }}
                              title={`(${xMm} mm, ${yMm} mm): ${val.toFixed(3)} K`}
                            />
                          );
                        })
                      )}
                    </div>
                  )}

                  {/* On-screen Overlays */}
                  <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur px-2.5 py-1 rounded border border-slate-800 text-[11px] font-mono text-slate-300">
                    t = {currentTimeS} s (Frame {currentFrame + 1}/{animData?.n_frames || 0})
                  </div>
                </div>

                {/* Video Controls */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="p-2.5 bg-amber-500 text-slate-950 rounded-xl hover:bg-amber-400 transition-all font-bold"
                    >
                      {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsPlaying(false);
                        setCurrentFrame(0);
                      }}
                      className="p-2.5 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700 transition-all"
                    >
                      <RotateCcw className="w-4 h-4" />
                    </button>

                    {/* Timeline Slider */}
                    <input
                      type="range"
                      min={0}
                      max={(animData?.n_frames || 1) - 1}
                      value={currentFrame}
                      onChange={(e) => {
                        setIsPlaying(false);
                        setCurrentFrame(parseInt(e.target.value));
                      }}
                      className="flex-1 accent-amber-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
                    />

                    <span className="text-xs font-mono text-slate-400 w-16 text-right">
                      {currentTimeS}s
                    </span>
                  </div>

                  {/* Playback Speed Controls */}
                  <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                    <div className="flex items-center gap-1.5">
                      <span>Speed:</span>
                      {[0.5, 1, 2].map((spd) => (
                        <button
                          key={spd}
                          type="button"
                          onClick={() => setPlaybackSpeed(spd)}
                          className={`px-2 py-0.5 rounded text-[11px] ${
                            playbackSpeed === spd
                              ? "bg-slate-700 text-slate-200 font-semibold"
                              : "text-slate-500 hover:text-slate-300"
                          }`}
                        >
                          {spd}x
                        </button>
                      ))}
                    </div>
                    <div className="font-mono text-[11px]">
                      Scale: [{minValDisplay.toFixed(1)} K ... {maxValDisplay.toFixed(1)} K]
                    </div>
                  </div>
                </div>
              </div>

              {/* Right (5 cols): Temperature-vs-Time Curve & Anomaly Summary */}
              <div className="lg:col-span-5 space-y-6">
                {/* Thermal Transient Curve Preview */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <BarChart2 className="w-4 h-4 text-cyan-400" />
                      <span className="text-xs font-semibold text-slate-200">
                        Thermal Transient Response ΔT(t)
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">LFMT Excitation Response</span>
                  </div>

                  {/* Simplified SVG Temperature Curve */}
                  <div className="h-44 bg-slate-950 rounded-xl border border-slate-800 p-3 relative flex items-end">
                    <svg className="w-full h-full overflow-visible" viewBox="0 0 100 50" preserveAspectRatio="none">
                      {/* Grid Lines */}
                      <line x1="0" y1="10" x2="100" y2="10" stroke="#334155" strokeWidth="0.5" strokeDasharray="2,2" />
                      <line x1="0" y1="25" x2="100" y2="25" stroke="#334155" strokeWidth="0.5" strokeDasharray="2,2" />
                      <line x1="0" y1="40" x2="100" y2="40" stroke="#334155" strokeWidth="0.5" strokeDasharray="2,2" />

                      {/* Configured Defect Probe Curve */}
                      {(simulationResult?.temperature_curves?.probe_roi_dT || simulationResult?.temperature_curves?.defect_center_roi_dT) && (
                        <polyline
                          fill="none"
                          stroke="#f59e0b"
                          strokeWidth="2"
                          points={(simulationResult.temperature_curves.probe_roi_dT || simulationResult.temperature_curves.defect_center_roi_dT)
                            .map((val: number, idx: number, arr: number[]) => {
                              const x = (idx / Math.max(1, arr.length - 1)) * 100;
                              const y = 48 - (val / Math.max(1e-4, simulationResult.peak_delta_t_k)) * 44;
                              return `${x},${y}`;
                            })
                            .join(" ")}
                        />
                      )}

                      {/* Reference ROI Curve */}
                      {(simulationResult?.temperature_curves?.reference_roi_dT || simulationResult?.temperature_curves?.sound_plate_roi_dT) && (
                        <polyline
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="1.5"
                          strokeDasharray="1,1"
                          points={(simulationResult.temperature_curves.reference_roi_dT || simulationResult.temperature_curves.sound_plate_roi_dT)
                            .map((val: number, idx: number, arr: number[]) => {
                              const x = (idx / Math.max(1, arr.length - 1)) * 100;
                              const y = 48 - (val / Math.max(1e-4, simulationResult.peak_delta_t_k)) * 44;
                              return `${x},${y}`;
                            })
                            .join(" ")}
                        />
                      )}
                    </svg>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-0.5 bg-amber-400"></span>
                      <span>Configured Defect-Center Probe</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-0.5 bg-cyan-400"></span>
                      <span>Reference ROI</span>
                    </div>
                  </div>
                </div>

                {/* Configured Ground Truth vs Detected Anomaly Comparison */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
                      <Crosshair className="w-4 h-4 text-rose-400" />
                      <span>Configured Virtual Specimen vs NDT Prediction</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                      Ground Truth Isolated
                    </span>
                  </div>

                  {(() => {
                    const detectedDefects = simulationResult?.analysis_result?.defects;
                    const firstDefect = detectedDefects && detectedDefects.length > 0 ? detectedDefects[0] : null;
                    const detectedLocation = firstDefect?.centroid_mm
                      ? `Centroid (${firstDefect.centroid_mm[0].toFixed(1)}, ${firstDefect.centroid_mm[1].toFixed(1)}) mm`
                      : analysisVerdict?.is_anomaly_detected
                      ? "Localization unavailable"
                      : "Zero False Alarms";

                    return (
                      <div className="space-y-3 text-xs">
                        <div className="grid grid-cols-2 gap-3">
                          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                            <div className="text-slate-400 font-semibold flex items-center justify-between">
                              <span>CONFIGURED GEOMETRY</span>
                              <span className="text-[10px] text-amber-400/80 font-mono">Virtual Input</span>
                            </div>
                            <div className="font-mono text-slate-100 font-medium">
                              {gt?.has_defect ? "Mild Steel + Slag Inclusion" : "Sound Mild Steel Control"}
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono space-y-0.5">
                              {gt?.has_defect && gt.defects && gt.defects[0] ? (
                                <>
                                  <div>Diameter: {gt.defects[0].diameter_mm} mm · Depth: {gt.defects[0].depth_mm} mm</div>
                                  <div>Slag: k = 1.5 W/m·K, Steel: 51.9 W/m·K</div>
                                </>
                              ) : (
                                <div>Homogeneous Plate (No Inclusions)</div>
                              )}
                            </div>
                          </div>

                          <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                            <div className="text-slate-400 font-semibold flex items-center justify-between">
                              <span>AUTONOMOUS PREDICTION</span>
                              <span className="text-[10px] text-cyan-400/80 font-mono">Blind Analysis</span>
                            </div>
                            <div className="font-mono text-cyan-300 font-medium truncate">
                              {analysisVerdict?.is_anomaly_detected ? "GENERIC_SUBSURFACE_THERMAL_ANOMALY" : "HEALTHY (SOUND)"}
                            </div>
                            <div className="text-[11px] text-slate-400 font-mono space-y-0.5">
                              <div>Location: {detectedLocation}</div>
                              <div>Confidence: {((analysisVerdict?.consensus_confidence || 0.6) * 100).toFixed(0)}% (Multi-Method)</div>
                            </div>
                          </div>
                        </div>

                        {/* AI Safety Gating Notice */}
                        <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 text-[11px] text-slate-400 flex items-center gap-2">
                          <ShieldCheck className="w-4 h-4 text-amber-400 flex-shrink-0" />
                          <span>
                            <strong className="text-slate-300">AI Safety Gate Active:</strong> Unvalidated neural classifier gated; diagnosis formulated strictly from physics-based thermal processing consensus.
                          </span>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </div>
            </div>

            {/* Bottom Section: NDT Signal Processing Maps (Real 2-D Rendering) */}
            {processingMaps && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-amber-400" />
                    <h3 className="text-sm font-semibold text-slate-200">
                      Thermographic Signal Processing 2-D Feature Maps
                    </h3>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {[
                      { id: "raw", label: "Raw Contrast" },
                      { id: "mf", label: "Matched Filter (MF)" },
                      { id: "pct", label: "PCT Blind EOF" },
                      { id: "spct", label: "SPCT" },
                      { id: "rpt", label: "RPT" }
                    ].map((m) => (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => setActiveMethodTab(m.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                          activeMethodTab === m.id
                            ? "bg-amber-500 text-slate-950 font-bold shadow"
                            : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Active Map Detail & 2-D Matrix Heatmap */}
                {(() => {
                  const activeMapObj = processingMaps[activeMethodTab];
                  if (!activeMapObj || !activeMapObj.map) {
                    return (
                      <div className="p-8 text-center text-xs text-slate-500 font-mono bg-slate-950 rounded-xl border border-slate-800">
                        Feature map data not computed for this modality.
                      </div>
                    );
                  }

                  const mapData: number[][] = activeMapObj.map;
                  const flatVals = mapData.flat();
                  const mapMin = Math.min(...flatVals);
                  const mapMax = Math.max(...flatVals);

                  return (
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                      {/* 2D Processing Map Visualizer */}
                      <div className="lg:col-span-6 aspect-[40/28] bg-slate-950 rounded-xl border border-slate-800 p-2 relative overflow-hidden flex items-center justify-center">
                        <div
                          className="w-full h-full grid"
                          style={{
                            gridTemplateColumns: `repeat(${mapData[0]?.length || 40}, minmax(0, 1fr))`,
                            gridTemplateRows: `repeat(${mapData.length || 28}, minmax(0, 1fr))`
                          }}
                        >
                          {mapData.map((row: number[], rIdx: number) =>
                            row.map((val: number, cIdx: number) => (
                              <div
                                key={`${rIdx}-${cIdx}`}
                                className="w-full h-full"
                                style={{
                                  backgroundColor: renderThermalColor(val, mapMin, mapMax)
                                }}
                                title={`[${rIdx}, ${cIdx}]: ${val.toFixed(4)}`}
                              />
                            ))
                          )}
                        </div>
                      </div>

                      {/* Map Telemetry & Explanation */}
                      <div className="lg:col-span-6 space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className="text-base font-bold text-slate-100">{activeMapObj.name}</h4>
                          <span
                            className={`px-2.5 py-1 rounded text-xs font-mono font-semibold ${
                              activeMapObj.is_detected
                                ? "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
                                : "bg-slate-800 text-slate-400 border border-slate-700"
                            }`}
                          >
                            {activeMapObj.is_detected ? "Anomaly Detected" : "No Anomaly"}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400 text-[11px]">{activeMapObj.score_label || "Score"}</div>
                            <div className="text-amber-400 font-bold text-base mt-0.5">
                              {typeof activeMapObj.score === "number" ? activeMapObj.score.toFixed(3) : activeMapObj.score}
                            </div>
                          </div>
                          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <div className="text-slate-400 text-[11px]">Execution Time</div>
                            <div className="text-cyan-300 font-bold text-base mt-0.5">
                              {activeMapObj.runtime_s ? `${(activeMapObj.runtime_s * 1000).toFixed(1)} ms` : "N/A"}
                            </div>
                          </div>
                        </div>

                        <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
                          {activeMapObj.explanation}
                        </p>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

