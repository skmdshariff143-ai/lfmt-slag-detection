import React from "react";
import { Layers, CheckCircle2, AlertTriangle } from "lucide-react";

export default function MaterialsPage() {
  const materials = [
    {
      name: "Mild Steel (AISI 1018)",
      k: 51.9,
      rho: 7850,
      cp: 486,
      alpha: "1.36 × 10⁻⁵",
      effusivity: "14,075",
      source: "Incropera et al., Fundamentals of Heat and Mass Transfer (2011)",
      status: "VERIFIED BENCHMARK",
      role: "Base Specimen Matrix",
    },
    {
      name: "Silicate Welding Slag",
      k: 1.20,
      rho: 2800,
      cp: 850,
      alpha: "5.04 × 10⁻⁷",
      effusivity: "1,690",
      source: "Mills (1993), Slag Atlas; Keene (1995)",
      status: "VERIFIED BENCHMARK",
      role: "Subsurface Inclusion",
    },
    {
      name: "Air Void / Delamination",
      k: 0.026,
      rho: 1.161,
      cp: 1007,
      alpha: "2.22 × 10⁻⁵",
      effusivity: "5.5",
      source: "NIST Standard Reference Database",
      status: "VERIFIED BENCHMARK",
      role: "Extreme Void Reference",
    },
    {
      name: "Stainless Steel (AISI 304)",
      k: 14.9,
      rho: 7900,
      cp: 477,
      alpha: "3.95 × 10⁻⁶",
      effusivity: "7,495",
      source: "Incropera et al. (2011)",
      status: "VERIFIED BENCHMARK",
      role: "Alternative Base Matrix",
    },
    {
      name: "High-TiO2 Rutile Slag",
      k: 1.45,
      rho: 2950,
      cp: 880,
      alpha: "5.58 × 10⁻⁷",
      effusivity: "1,940",
      source: "Preliminary Literature Estimates",
      status: "EXPLORATORY / NOT IN PRIMARY BENCHMARK",
      role: "Future Physical Testing",
    },
  ];

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs">
          <Layers className="w-4 h-4" />
          <span>THERMOPHYSICAL PROPERTIES</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Thermophysical Material Property Database
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Comprehensive database of structural mild steel and welding slag inclusion thermophysical properties with literature citations and verification statuses.
        </p>
      </div>

      {/* Materials Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300 font-mono">
            <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] border-b border-slate-800">
              <tr>
                <th className="px-3 py-3">Material</th>
                <th className="px-3 py-3 text-right">\(k\) [W/m·K]</th>
                <th className="px-3 py-3 text-right">\(\rho\) [kg/m³]</th>
                <th className="px-3 py-3 text-right">\(C_p\) [J/kg·K]</th>
                <th className="px-3 py-3 text-right">\(\alpha\) [m²/s]</th>
                <th className="px-3 py-3 text-right">Effusivity [W·s½/m²K]</th>
                <th className="px-3 py-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {materials.map((m) => {
                const isVerified = m.status === "VERIFIED BENCHMARK";
                return (
                  <tr key={m.name} className="hover:bg-slate-950/40">
                    <td className="px-3 py-3.5">
                      <div className="font-bold text-slate-100">{m.name}</div>
                      <div className="text-[10px] text-slate-500">{m.role} • {m.source}</div>
                    </td>
                    <td className="px-3 py-3.5 text-right font-semibold text-cyan-300">{m.k.toFixed(3)}</td>
                    <td className="px-3 py-3.5 text-right">{m.rho}</td>
                    <td className="px-3 py-3.5 text-right">{m.cp}</td>
                    <td className="px-3 py-3.5 text-right text-slate-400">{m.alpha}</td>
                    <td className="px-3 py-3.5 text-right font-semibold text-indigo-300">{m.effusivity}</td>
                    <td className="px-3 py-3.5 text-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium border ${
                          isVerified
                            ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/50"
                            : "bg-amber-950/40 text-amber-300 border-amber-800/50"
                        }`}
                      >
                        {isVerified ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                        {isVerified ? "VERIFIED SOURCE" : "EXPLORATORY"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}