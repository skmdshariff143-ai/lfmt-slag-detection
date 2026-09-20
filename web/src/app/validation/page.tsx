import React from "react";
import { CheckCircle2, ShieldAlert, Cpu, Layers, Clock } from "lucide-react";

export default function ValidationPage() {
  const fdmFemRows = [
    {
      case: "Homogeneous Mild Steel Plate",
      fdm: "22.70 °C",
      fem: "22.72 °C",
      diff: "0.046 K",
      l2: "0.13%",
      status: "PASS",
    },
    {
      case: "Plate with Subsurface Slag Inclusion",
      fdm: "23.21 °C",
      fem: "22.91 °C",
      diff: "0.690 K",
      l2: "0.20%",
      status: "PASS",
    },
  ];

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs">
          <CheckCircle2 className="w-4 h-4" />
          <span>NUMERICAL & PHYSICAL VALIDATION</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Numerical Verification & Solvers Cross-Validation
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Multi-tiered verification confirming physical sanity, 3D FEM vs 3D FDM mathematical convergence, spatial grid independence, and temporal time-step stability.
        </p>
      </div>

      {/* Info Warning Banner */}
      <div className="p-4 rounded-lg bg-slate-900 border border-cyan-800/40 text-xs text-slate-300 space-y-1">
        <div className="font-semibold text-cyan-300 flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-cyan-400" />
          Scope of Validation Notice
        </div>
        <p className="text-slate-400 leading-relaxed">
          This project has not yet been validated using a physical specimen and laboratory infrared camera. Current validation strictly concerns numerical consistency, mathematical cross-validation between independent FDM/FEM partial differential equation solvers, and simulation reproducibility.
        </p>
      </div>

      {/* 1. FEM vs FDM Cross-Validation */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h2 className="text-sm font-semibold text-white font-mono uppercase tracking-wider flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            3D FEM vs 3D FDM Independent Cross-Validation
          </h2>
          <span className="text-xs font-mono text-emerald-400">Relative L2 &lt; 0.25%</span>
        </div>

        <p className="text-xs text-slate-400">
          Two completely independent numerical engines solve the identical 3D transient heat diffusion problem on a 100 &times; 70 &times; 2.3 mm mild steel plate:
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300 font-mono">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-2.5">Scenario</th>
                <th className="px-3 py-2.5 text-center">FDM Peak Surface T</th>
                <th className="px-3 py-2.5 text-center">FEM Peak Surface T</th>
                <th className="px-3 py-2.5 text-center">Max Abs Difference</th>
                <th className="px-3 py-2.5 text-center">Relative L2 Error</th>
                <th className="px-3 py-2.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {fdmFemRows.map((r, i) => (
                <tr key={i} className="hover:bg-slate-950/40">
                  <td className="px-3 py-2.5 font-bold text-slate-200">{r.case}</td>
                  <td className="px-3 py-2.5 text-center">{r.fdm}</td>
                  <td className="px-3 py-2.5 text-center">{r.fem}</td>
                  <td className="px-3 py-2.5 text-center text-cyan-300 font-semibold">{r.diff}</td>
                  <td className="px-3 py-2.5 text-center text-emerald-400 font-bold">{r.l2}</td>
                  <td className="px-3 py-2.5 text-center">
                    <span className="px-2 py-0.5 rounded bg-emerald-950/40 text-emerald-300 border border-emerald-800/50">
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Physics Sanity Tests */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-200 font-semibold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Physics Sanity Checks
          </h3>
          <ul className="space-y-2 text-xs font-mono text-slate-300 divide-y divide-slate-800/60">
            <li className="pt-2 flex items-center justify-between">
              <span>Energy Conservation (Monotonic Heating):</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
            <li className="pt-2 flex items-center justify-between">
              <span>Cooling Period Monotonic Decay:</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
            <li className="pt-2 flex items-center justify-between">
              <span>Boundary Robin Flux Balance:</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
            <li className="pt-2 flex items-center justify-between">
              <span>Harmonic Mean Thermal Resistance:</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
          </ul>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
          <h3 className="text-xs font-mono uppercase text-slate-200 font-semibold flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-400" />
            Convergence Benchmarks
          </h3>
          <ul className="space-y-2 text-xs font-mono text-slate-300 divide-y divide-slate-800/60">
            <li className="pt-2 flex items-center justify-between">
              <span>Spatial Mesh Convergence (L<sub>2</sub> &lt; 0.8%):</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
            <li className="pt-2 flex items-center justify-between">
              <span>Time-Step Convergence (&Delta;t = 0.04 s):</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
            <li className="pt-2 flex items-center justify-between">
              <span>Implicit Euler Unconditional Stability:</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
            <li className="pt-2 flex items-center justify-between">
              <span>SuperLU Pre-Factored LU Inversion:</span>
              <span className="text-emerald-400 font-bold">PASS</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}