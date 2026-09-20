import React from "react";
import Link from "next/link";
import { Github, FileCode, CheckCircle2 } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950 text-slate-400 text-xs py-10 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-2 md:col-span-2">
            <h4 className="text-slate-200 font-semibold text-sm">
              Linear Frequency-Modulated Thermography (LFMT) Research
            </h4>
            <p className="text-slate-400 leading-relaxed text-xs max-w-md">
              A simulation-based computational non-destructive testing (NDT) benchmark for detecting, sizing, and characterizing subsurface welding slag inclusions in structural mild steel plates using 3D Finite Element Method forward modeling and blind signal processing.
            </p>
            <div className="pt-2 text-slate-500 font-mono text-[11px]">
              Author: Project Team • Final Year Research Capstone • MIT Licensed
            </div>
          </div>

          <div>
            <h4 className="text-slate-200 font-semibold text-sm mb-2">Scientific Navigation</h4>
            <ul className="space-y-1.5">
              <li><Link href="/conference" className="hover:text-cyan-400 transition-colors">Conference Mode</Link></li>
              <li><Link href="/results" className="hover:text-cyan-400 transition-colors">Benchmark Results</Link></li>
              <li><Link href="/sensitivity" className="hover:text-cyan-400 transition-colors">Parameter Sensitivity</Link></li>
              <li><Link href="/validation" className="hover:text-cyan-400 transition-colors">Numerical Validation</Link></li>
              <li><Link href="/methodology" className="hover:text-cyan-400 transition-colors">Mathematical Formulations</Link></li>
              <li><Link href="/materials" className="hover:text-cyan-400 transition-colors">Material Database</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-slate-200 font-semibold text-sm mb-2">Reproducibility</h4>
            <ul className="space-y-1.5 font-mono text-[11px]">
              <li className="flex items-center gap-1.5 text-slate-400">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>34 / 34 Tests Passing</span>
              </li>
              <li className="flex items-center gap-1.5 text-slate-400">
                <FileCode className="w-3 h-3 text-cyan-400" />
                <span>Zero Data Leakage (Blind)</span>
              </li>
              <li className="pt-2">
                <a
                  href="https://github.com/skmdshariff143-ai/lfmt-slag-detection"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-slate-300 hover:text-white font-sans text-xs"
                >
                  <Github className="w-3.5 h-3.5" />
                  View GitHub Repository
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800/60 mt-8 pt-6 flex flex-wrap items-center justify-between gap-2 text-slate-500 text-[11px]">
          <div>
            © 2026 LFMT Research Project. Released under the MIT License.
          </div>
          <div className="font-mono text-slate-400">
            Numerical Simulation Benchmark • No Physical Infrared Camera Validation Claimed
          </div>
        </div>
      </div>
    </footer>
  );
};