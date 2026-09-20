import React from "react";
import { MaxDepthRecord } from "@/types/research";

interface MaxDepthMatrixProps {
  data: MaxDepthRecord[];
  selectedNoise?: string;
}

export const MaxDepthMatrix: React.FC<MaxDepthMatrixProps> = ({
  data,
  selectedNoise = "SNR 30 dB",
}) => {
  const filtered = data.filter((d) => d.noise_condition === selectedNoise);
  const diameters = Array.from(new Set(filtered.map((d) => d.diameter_mm))).sort((a, b) => a - b);
  const methods = Array.from(new Set(filtered.map((d) => d.method)));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-left text-slate-300 border border-slate-800 rounded-lg overflow-hidden">
        <thead className="bg-slate-900/80 text-slate-200 uppercase font-mono text-[11px] border-b border-slate-800">
          <tr>
            <th className="px-4 py-3">Method</th>
            {diameters.map((d) => (
              <th key={d} className="px-4 py-3 text-center">
                D = {d.toFixed(1)} mm
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-mono">
          {methods.map((m) => (
            <tr key={m} className="hover:bg-slate-900/40 transition-colors">
              <td className="px-4 py-3 font-semibold text-slate-200">{m}</td>
              {diameters.map((d) => {
                const match = filtered.find((r) => r.method === m && r.diameter_mm === d);
                const zVal = match ? match.max_detectable_depth_mm : 0.0;
                const isDetected = zVal > 0.0;
                return (
                  <td key={d} className="px-4 py-3 text-center">
                    <span
                      className={`inline-block px-2.5 py-1 rounded text-xs font-medium border ${
                        isDetected
                          ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/50"
                          : "bg-slate-900 text-slate-500 border-slate-800"
                      }`}
                    >
                      {isDetected ? `z ≤ ${zVal.toFixed(1)} mm` : "< 0.2 mm"}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};