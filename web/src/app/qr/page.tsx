import React from "react";
import { QrCode, Globe, GitFork, ExternalLink, Sparkles } from "lucide-react";

export const metadata = {
  title: "QR Codes & Conference Links | LFMT Slag Detection",
  description: "Scannable QR codes and quick access links for conference attendees and reviewers.",
};

export default function QRPage() {
  const repoUrl = "https://github.com/skmdshariff143-ai/lfmt-slag-detection";
  const webPortalUrl = "https://web-kappa-woad-56.vercel.app";

  // Public QR code generators (reliable, high contrast, SVG/PNG)
  const repoQrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(repoUrl)}&bgcolor=0f172a&color=38bdf8&margin=10`;
  const portalQrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(webPortalUrl)}&bgcolor=0f172a&color=34d399&margin=10`;

  return (
    <div className="space-y-10 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 font-mono text-xs uppercase tracking-wider">
          <QrCode className="w-3.5 h-3.5" />
          <span>Conference Quick Access</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-slate-100">Scan & Explore on Mobile</h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          Scan the QR codes below to access the live conference web application and explore the open-source
          simulation repository directly from your mobile device.
        </p>
      </div>

      {/* QR Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Web Portal QR */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center text-center space-y-6 shadow-xl">
          <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs uppercase tracking-wider font-semibold">
            <Globe className="w-4 h-4" />
            <span>Interactive Web Portal</span>
          </div>

          {/* QR Code Container */}
          <div className="p-3 bg-slate-950 rounded-2xl border-2 border-emerald-500/30 shadow-lg shadow-emerald-500/10">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={portalQrUrl}
              alt="QR Code for Live Conference Web Portal"
              className="w-56 h-56 rounded-xl object-contain"
              loading="eager"
            />
          </div>

          <div className="space-y-2">
            <div className="text-base font-bold text-slate-200">Live Conference Dashboard</div>
            <div className="text-xs font-mono text-slate-400 break-all">{webPortalUrl}</div>
          </div>

          <a
            href={webPortalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs rounded-xl transition-all shadow-lg shadow-emerald-500/20"
          >
            <span>Open Portal Link</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* GitHub Repository QR */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center text-center space-y-6 shadow-xl">
          <div className="flex items-center gap-2 text-sky-400 font-mono text-xs uppercase tracking-wider font-semibold">
            <GitFork className="w-4 h-4" />
            <span>GitHub Repository</span>
          </div>

          {/* QR Code Container */}
          <div className="p-3 bg-slate-950 rounded-2xl border-2 border-sky-500/30 shadow-lg shadow-sky-500/10">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={repoQrUrl}
              alt="QR Code for GitHub Repository"
              className="w-56 h-56 rounded-xl object-contain"
              loading="eager"
            />
          </div>

          <div className="space-y-2">
            <div className="text-base font-bold text-slate-200">Open-Source Code & Benchmarks</div>
            <div className="text-xs font-mono text-slate-400 break-all">{repoUrl}</div>
          </div>

          <a
            href={repoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs rounded-xl transition-all shadow-lg shadow-sky-500/20"
          >
            <span>Open GitHub Repo</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Projection Tip */}
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-center gap-4 text-xs text-slate-400">
        <Sparkles className="w-5 h-5 text-amber-400 shrink-0" />
        <div>
          <strong className="text-slate-200">Conference Presentation Tip:</strong> You can display this page in
          fullscreen during Q&A or poster sessions for seamless audience smartphone scanning.
        </div>
      </div>
    </div>
  );
}
