import React from "react";
import { Info, GitFork, BookOpen, Terminal, CheckCircle2, ShieldCheck, FileText, Code2, AlertTriangle } from "lucide-react";

export const metadata = {
  title: "About the Research | LFMT Slag Detection",
  description: "Research background, B.Tech ECE capstone context, scientific methodology, and software citation.",
};

export default function AboutPage() {
  return (
    <div className="space-y-12 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sky-400 font-mono text-xs uppercase tracking-wider mb-2">
          <Info className="w-4 h-4" />
          <span>Research Context & Provenance</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-100">About This Research</h1>
        <p className="text-slate-400 text-base mt-2 leading-relaxed">
          Linear Frequency-Modulated Infrared Thermography (LFMT) for Subsurface Slag Inclusion Detection in Mild Steel:
          A Rigorous 3-D FEM Simulation Benchmark and Comparative Study.
        </p>
      </div>

      {/* Project Background & Motivation */}
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-4 shadow-sm">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-sky-400" />
          <span>Project Background & Motivation</span>
        </h2>
        <div className="text-slate-300 text-sm leading-relaxed space-y-3">
          <p>
            Slag inclusions are among the most common and structurally compromising volumetric defects in structural steel welding,
            occurring when molten flux and non-metallic oxides become trapped within the solidifying weld pool. Left undetected,
            subsurface slag inclusions act as high stress-concentration sites, initiating microcracks and catastrophic fatigue failure
            in pressure vessels, pipelines, and bridge structures.
          </p>
          <p>
            Conventional non-destructive testing (NDT) methods like ultrasonic testing (UT) and radiographic testing (RT) require
            either acoustic couplants or hazardous ionizing radiation. <strong>Linear Frequency-Modulated Infrared Thermography (LFMT)</strong> offers
            a non-contact, single-sided, couplant-free, and eye-safe active thermographic alternative that combines the high energy
            concentration of lock-in thermography with the multi-depth probing capability of pulsed thermography.
          </p>
        </div>
      </section>

      {/* Numerical Benchmark Design */}
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-6 shadow-sm">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-sky-400" />
          <span>Benchmark Architecture & Scope</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <div className="text-xs font-mono uppercase text-sky-400 font-bold">Physics Simulation</div>
            <p className="text-xs text-slate-300 leading-relaxed">
              3-D transient heat diffusion modeled via high-resolution Finite Element Method (<code className="text-sky-300">scikit-fem</code>)
              and cross-validated against an independent Finite Difference Method (FDM) solver.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <div className="text-xs font-mono uppercase text-emerald-400 font-bold">Statistical Rigor</div>
            <p className="text-xs text-slate-300 leading-relaxed">
              <strong>4,030 total method evaluations</strong> across 25 defect geometries (&Oslash; 4&ndash;12 mm, depth 0.2&ndash;1.0 mm),
              healthy controls, 10 deterministic noise seeds, and 4 noise regimes (Clean, 30 dB, 25 dB, 20 dB).
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <div className="text-xs font-mono uppercase text-purple-400 font-bold">Post-Processing Methods</div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Systematic comparison of 5 distinct processing paradigms: Principal Component Thermography (PCT),
              Matched Filter / Pulse Compression, Segmented PCT (SPCT), Reconstructed Phase Thermography (RPT), and Raw Contrast.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
            <div className="text-xs font-mono uppercase text-amber-400 font-bold">Rigorous Nomenclature</div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Strictly enforces honest metric reporting: localization errors reported strictly on detected cases with &ldquo;N/A&rdquo; for missed targets,
              and independent false positive verification on healthy plates.
            </p>
          </div>
        </div>
      </section>

      {/* Key Research Findings Summary */}
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-4 shadow-sm">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span>Key Findings & Takeaways</span>
        </h2>
        <ul className="space-y-3 text-sm text-slate-300 list-disc list-inside leading-relaxed">
          <li>
            <strong className="text-slate-100">PCT Superiority:</strong> Principal Component Thermography (EOF-2) demonstrated the highest overall detection rate (<strong>62.3%</strong>),
            highest segmentation quality (mean IoU = <strong>0.301</strong>, Dice = <strong>0.395</strong>), and lowest localization error (<strong>1.13 mm</strong>).
          </li>
          <li>
            <strong className="text-slate-100">Zero False Positives:</strong> PCT and SPCT maintained <strong>100% healthy control specificity (0% FPR)</strong> across all noise seeds down to 20 dB SNR.
          </li>
          <li>
            <strong className="text-slate-100">Depth Limits:</strong> Slag inclusions at depths &le; 0.4 mm are reliably detectable across all noise conditions; defects at depths &ge; 0.8 mm require low-noise environments (SNR &ge; 30 dB).
          </li>
        </ul>
      </section>

      {/* Scope Disclaimer */}
      <section className="bg-amber-950/20 border border-amber-500/30 rounded-2xl p-6 space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>Research Scope & Simulation Provenance</span>
        </div>
        <p className="text-xs text-amber-200/80 leading-relaxed">
          This work represents a <strong>rigorous numerical and computational benchmark study</strong> using verified 3-D finite element
          and finite difference transient heat diffusion simulations. Synthetic camera thermograms incorporate physical noise models (Gaussian white noise,
          detector sensitivity, quantization). While calibrated to published material thermophysical constants of mild steel and flux slag,
          experimental validation on physical steel specimens with experimental infrared cameras remains a planned direction for future work.
        </p>
      </section>

      {/* Software Citation */}
      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-8 space-y-4 shadow-sm">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Code2 className="w-5 h-5 text-sky-400" />
          <span>Software Citation</span>
        </h2>
        <p className="text-xs text-slate-400">
          If you use or reference this benchmark code or dataset in academic research, please cite the software package:
        </p>
        <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 font-mono text-xs text-sky-300 overflow-x-auto">
{`@software{lfmt_slag_detection_2026,
  author       = {Project Team},
  title        = {Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion Detection in Mild Steel: 3-D FEM Benchmark and Analysis Framework},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/skmdshariff143-ai/lfmt-slag-detection}
}`}
        </pre>
      </section>

      {/* Open Source Links */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-6 bg-slate-900 border border-slate-800 rounded-2xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
            <GitFork className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-200">Open-Source Codebase</div>
            <div className="text-xs text-slate-400">GitHub: skmdshariff143-ai/lfmt-slag-detection</div>
          </div>
        </div>
        <a
          href="https://github.com/skmdshariff143-ai/lfmt-slag-detection"
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white font-medium text-xs rounded-lg transition-colors shadow-lg shadow-sky-500/20"
        >
          View on GitHub →
        </a>
      </div>
    </div>
  );
}
