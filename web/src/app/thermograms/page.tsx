"use client";

import React, { useState, useEffect, useRef } from "react";
import { Play, Pause, RotateCcw, Flame, Info, ChevronRight, Activity } from "lucide-react";

interface FrameData {
  frame_index: number;
  time_seconds: number;
  image_url: string;
  min_temp_c: number;
  max_temp_c: number;
  mean_temp_c: number;
}

interface CaseOption {
  tag: string;
  label: string;
  diameter_mm: number;
  depth_mm: number;
  is_healthy: boolean;
}

const CASES: CaseOption[] = [
  { tag: "D080_Z004", label: "Defect (Ø8mm @ 0.4mm depth)", diameter_mm: 8.0, depth_mm: 0.4, is_healthy: false },
  { tag: "D040_Z002", label: "Defect (Ø4mm @ 0.2mm depth)", diameter_mm: 4.0, depth_mm: 0.2, is_healthy: false },
  { tag: "D060_Z004", label: "Defect (Ø6mm @ 0.4mm depth)", diameter_mm: 6.0, depth_mm: 0.4, is_healthy: false },
  { tag: "D100_Z006", label: "Defect (Ø10mm @ 0.6mm depth)", diameter_mm: 10.0, depth_mm: 0.6, is_healthy: false },
  { tag: "D120_Z008", label: "Defect (Ø12mm @ 0.8mm depth)", diameter_mm: 12.0, depth_mm: 0.8, is_healthy: false },
  { tag: "HEALTHY_CONTROL", label: "Healthy Control (No defect)", diameter_mm: 0.0, depth_mm: 0.0, is_healthy: true },
];

export default function ThermogramsPage() {
  const [selectedCase, setSelectedCase] = useState<string>("D080_Z004");
  const [frames, setFrames] = useState<FrameData[]>([]);
  const [currentFrameIdx, setCurrentFrameIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1); // 1x = ~1 frame per 500ms
  const [loading, setLoading] = useState<boolean>(true);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Load case metadata on change
  useEffect(() => {
    async function loadCase() {
      setLoading(true);
      try {
        const res = await fetch(`/cases/${selectedCase}.json`);
        if (res.ok) {
          const data = await res.json();
          setFrames(data.frames || []);
          setCurrentFrameIdx(0);
        }
      } catch (err) {
        console.error("Failed to load frames:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCase();
  }, [selectedCase]);

  // Animation Loop
  useEffect(() => {
    if (isPlaying && frames.length > 0) {
      const intervalMs = 600 / playbackSpeed;
      timerRef.current = setInterval(() => {
        setCurrentFrameIdx((prev) => (prev + 1) % frames.length);
      }, intervalMs);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, frames.length]);

  const currentFrame = frames[currentFrameIdx] || {
    frame_index: 0,
    time_seconds: 0.0,
    image_url: `/thermograms/${selectedCase}/frame_00.png`,
    min_temp_c: 20.0,
    max_temp_c: 20.0,
    mean_temp_c: 20.0,
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sky-400 font-mono text-xs uppercase tracking-wider mb-2">
          <Flame className="w-4 h-4" />
          <span>Interactive Thermogram Playback</span>
        </div>
        <h1 className="text-3xl font-bold text-slate-100">Virtual IR Camera Sequence Scrubber</h1>
        <p className="text-slate-400 text-sm mt-1 max-w-3xl">
          Observe transient surface thermal diffusion on mild steel plates across the 10-second LFMT linear frequency sweep
          (0.05 Hz &rarr; 0.50 Hz chirp excitation over 10.0 s, part of 12.0 s total observation time).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Player & Controls */}
        <div className="lg:col-span-2 space-y-6">
          {/* Main Thermogram Viewer */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-mono font-medium text-slate-300">
                  {selectedCase} — Frame {currentFrameIdx + 1} / {frames.length || 10}
                </span>
              </div>
              <div className="text-xs font-mono bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-sky-400">
                t = {currentFrame.time_seconds.toFixed(2)} s
              </div>
            </div>

            {/* Display Screen */}
            <div className="relative aspect-[4/3] w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
              {loading ? (
                <div className="text-slate-500 font-mono text-sm animate-pulse">Loading frame sequence...</div>
              ) : (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={currentFrame.image_url}
                  alt={`Thermogram at t=${currentFrame.time_seconds}s`}
                  className="w-full h-full object-contain select-none"
                />
              )}

              {/* HUD Overlay */}
              <div className="absolute top-3 left-3 bg-slate-950/80 backdrop-blur-md px-3 py-2 rounded border border-slate-800/80 font-mono text-[11px] space-y-0.5 text-slate-300">
                <div>T_max: <span className="text-rose-400 font-bold">{currentFrame.max_temp_c.toFixed(2)} °C</span></div>
                <div>T_mean: <span className="text-amber-400 font-bold">{currentFrame.mean_temp_c.toFixed(2)} °C</span></div>
                <div>T_min: <span className="text-sky-400 font-bold">{currentFrame.min_temp_c.toFixed(2)} °C</span></div>
              </div>
            </div>

            {/* Scrubber & Playback Controls */}
            <div className="space-y-4 pt-2">
              {/* Range Slider */}
              <div className="space-y-1">
                <div className="flex justify-between text-[11px] font-mono text-slate-400">
                  <span>0.0 s (Chirp Start)</span>
                  <span>Sweep t = {currentFrame.time_seconds.toFixed(1)} s</span>
                  <span>10.0 s (Chirp End)</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={Math.max(0, frames.length - 1)}
                  value={currentFrameIdx}
                  onChange={(e) => {
                    setIsPlaying(false);
                    setCurrentFrameIdx(Number(e.target.value));
                  }}
                  className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-400"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-xs transition-all ${
                      isPlaying
                        ? "bg-amber-500 hover:bg-amber-600 text-slate-950"
                        : "bg-sky-500 hover:bg-sky-600 text-white shadow-lg shadow-sky-500/20"
                    }`}
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    <span>{isPlaying ? "Pause" : "Play Sequence"}</span>
                  </button>

                  <button
                    onClick={() => {
                      setIsPlaying(false);
                      setCurrentFrameIdx(0);
                    }}
                    className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                    title="Reset to frame 0"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>

                {/* Speed Selector */}
                <div className="flex items-center gap-1.5 text-xs font-mono">
                  <span className="text-slate-400">Speed:</span>
                  {[0.5, 1, 2].map((spd) => (
                    <button
                      key={spd}
                      onClick={() => setPlaybackSpeed(spd)}
                      className={`px-2 py-1 rounded text-xs transition-colors ${
                        playbackSpeed === spd
                          ? "bg-slate-800 text-sky-400 border border-slate-700 font-bold"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {spd}x
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Specimen Selector & Physics Insight */}
        <div className="space-y-6">
          {/* Specimen Case Picker */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Select Specimen Case
            </h3>
            <div className="space-y-2">
              {CASES.map((c) => (
                <button
                  key={c.tag}
                  onClick={() => setSelectedCase(c.tag)}
                  className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between ${
                    selectedCase === c.tag
                      ? "bg-sky-500/15 border-sky-400 text-sky-200"
                      : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div>
                    <div className="text-xs font-mono font-bold text-slate-200">{c.tag}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{c.label}</div>
                  </div>
                  <ChevronRight className={`w-4 h-4 ${selectedCase === c.tag ? "text-sky-400" : "text-slate-600"}`} />
                </button>
              ))}
            </div>
          </div>

          {/* Thermal Diffusion Physics Info Box */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-sky-400">
              <Activity className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono">Chirp Physics Note</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Under LFMT linear frequency excitation f(t) = 0.1 + 0.09t Hz, the thermal penetration depth
              decreases over time as frequency increases:
            </p>
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 font-mono text-[11px] text-sky-300 text-center">
              &mu;(t) = &radic;(&alpha; / (&pi; f(t)))
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Early low frequencies (0.1 Hz, &mu; &asymp; 6.8 mm) probe deeper slag inclusions,
              while later higher frequencies (1.0 Hz, &mu; &asymp; 2.1 mm) confine energy to the near-surface
              region, yielding distinct phase and principal component signatures.
            </p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-slate-400">
              <Info className="w-4 h-4 text-sky-400" />
              <span>Inspect post-processed contrast maps</span>
            </div>
            <a
              href={`/explorer?case=${selectedCase}`}
              className="text-sky-400 hover:text-sky-300 font-mono font-medium underline"
            >
              Open in Explorer →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
