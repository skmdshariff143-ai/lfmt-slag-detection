import React from "react";
import { FileText, Cpu, Eye, Workflow, Sparkles } from "lucide-react";
import { KaTeXMath } from "@/components/KaTeXMath";

export default function MethodologyPage() {
  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-indigo-400 font-mono text-xs">
          <FileText className="w-4 h-4" />
          <span>MATHEMATICAL & NUMERICAL FORMULATION</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          LFMT Governing Equations & Signal Processing Theory
        </h1>
        <p className="text-slate-400 text-xs sm:text-sm max-w-3xl">
          Detailed mathematical derivations of transient 3D thermal diffusion, LFMT linear chirp waveforms, matched filtering pulse compression, and blind subspace decompositions.
        </p>
      </div>

      {/* Section 1: 3D Transient Heat Conduction */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-cyan-500/20 text-cyan-300 flex items-center justify-center text-xs">1</span>
          3-D Transient Heat Diffusion PDE & Boundary Conditions
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The non-homogeneous heat conduction equation across heterogeneous structural mild steel containing an embedded slag inclusion is formulated as:
        </p>
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-center font-mono">
          <KaTeXMath math="\rho(\mathbf{x}) C_p(\mathbf{x}) \frac{\partial T(\mathbf{x}, t)}{\partial t} = \nabla \cdot \left[ k(\mathbf{x}) \nabla T(\mathbf{x}, t) \right] + Q(\mathbf{x}, t)" block />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono text-slate-400">
          <div className="p-3 rounded bg-slate-950 border border-slate-800/80 space-y-1">
            <strong className="text-slate-200">Front Heated Surface (\(z = 0\)):</strong>
            <KaTeXMath math="-k \left.\frac{\partial T}{\partial z}\right|_{z=0} = q(t) - h_{\text{conv}}(T - T_{\text{amb}})" block />
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800/80 space-y-1">
            <strong className="text-slate-200">Rear Surface (\(z = L_z\)):</strong>
            <KaTeXMath math="-k \left.\frac{\partial T}{\partial z}\right|_{z=L_z} = h_{\text{conv}}(T - T_{\text{amb}})" block />
          </div>
        </div>
      </div>

      {/* Section 2: LFMT Chirp Waveform */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-cyan-500/20 text-cyan-300 flex items-center justify-center text-xs">2</span>
          Linear Frequency-Modulated Chirp Excitation
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The incident heat flux sweeps linearly across frequency band [f<sub>0</sub>, f<sub>1</sub>] over duration T<sub>exc</sub>:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono text-slate-300">
          <div className="p-3 rounded bg-slate-950 border border-slate-800 text-center space-y-1">
            <span className="text-slate-400 text-[11px]">Chirp Sweep Rate</span>
            <KaTeXMath math="\beta = \frac{f_1 - f_0}{T_{\text{exc}}}" block />
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800 text-center space-y-1">
            <span className="text-slate-400 text-[11px]">Instantaneous Phase</span>
            <KaTeXMath math="\phi(t) = 2\pi\left(f_0 t + \frac{1}{2}\beta t^2\right)" block />
          </div>
          <div className="p-3 rounded bg-slate-950 border border-slate-800 text-center space-y-1">
            <span className="text-slate-400 text-[11px]">Heat Flux Waveform</span>
            <KaTeXMath math="q(t) = q_0 [1 + \sin(\phi(t))]" block />
          </div>
        </div>
      </div>

      {/* Section 3: Signal Processing Algorithms */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-cyan-500/20 text-cyan-300 flex items-center justify-center text-xs">3</span>
          Thermographic Processing Modalities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono text-slate-300">
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
            <h3 className="font-bold text-cyan-400 text-sm">Matched Filtering (Pulse Compression)</h3>
            <p className="text-slate-400 text-[11px]">
              Cross-correlates each pixel&apos;s AC temperature response with reference chirp q<sub>ref</sub>(t):
            </p>
            <KaTeXMath math="R_{xy}(\tau) = \mathcal{F}^{-1}\left\{ \mathcal{F}\{T_{xy}^{\text{AC}}(t)\} \cdot \mathcal{F}^*\{q_{\text{ref}}(t)\} \right\}" block />
          </div>

          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
            <h3 className="font-bold text-emerald-400 text-sm">Principal Component Thermography (PCT)</h3>
            <p className="text-slate-400 text-[11px]">
              Singular Value Decomposition of standardized raster matrix A &isin; &reals;<sup>N<sub>t</sub> &times; N<sub>p</sub></sup>:
            </p>
            <KaTeXMath math="\mathbf{A} = \mathbf{U}\mathbf{\Sigma}\mathbf{V}^T, \quad \text{EOF}_k = \mathbf{v}_k" block />
          </div>
        </div>
      </div>
    </div>
  );
}