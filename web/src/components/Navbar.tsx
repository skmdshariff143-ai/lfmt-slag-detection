"use client";
import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Activity, 
  BarChart3, 
  FileText, 
  Layers, 
  Sliders, 
  CheckCircle2, 
  Eye, 
  Film, 
  QrCode, 
  Github, 
  Menu, 
  X,
  Presentation,
  Sparkles
} from "lucide-react";

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { name: "Conference", href: "/conference", icon: Presentation, highlight: true },
    { name: "Analyzer", href: "/analyze", icon: Sparkles, highlight: true },
    { name: "Results", href: "/results", icon: BarChart3 },
    { name: "Explorer", href: "/explorer", icon: Eye },
    { name: "Thermograms", href: "/thermograms", icon: Film },
    { name: "Sensitivity", href: "/sensitivity", icon: Sliders },
    { name: "Validation", href: "/validation", icon: CheckCircle2 },
    { name: "Methodology", href: "/methodology", icon: FileText },
    { name: "Materials", href: "/materials", icon: Layers },
    { name: "About", href: "/about", icon: Activity },
    { name: "QR", href: "/qr", icon: QrCode },
  ];

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-mono font-bold text-sm">
                LF
              </div>
              <div>
                <span className="text-white font-semibold tracking-tight text-sm sm:text-base">
                  LFMT Slag Detection
                </span>
                <span className="hidden sm:inline-block ml-2 text-xs font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  FEM 3D
                </span>
              </div>
            </Link>
          </div>

          <div className="hidden xl:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    item.highlight
                      ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/20"
                      : isActive
                      ? "bg-slate-800 text-white border border-slate-700"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {item.name}
                </Link>
              );
            })}

            <a
              href="https://github.com/skmdshariff143-ai/lfmt-slag-detection"
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 transition-colors"
            >
              <Github className="w-3.5 h-3.5" />
              GitHub
            </a>
          </div>

          <div className="xl:hidden flex items-center gap-2">
            <Link
              href="/conference"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/30"
            >
              <Presentation className="w-3.5 h-3.5" />
              Conference
            </Link>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-900 focus:outline-none"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="xl:hidden border-t border-slate-800 bg-slate-950 px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium ${
                  isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white hover:bg-slate-900"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}
          <a
            href="https://github.com/skmdshariff143-ai/lfmt-slag-detection"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-900"
          >
            <Github className="w-4 h-4" />
            GitHub Repository
          </a>
        </div>
      )}
    </nav>
  );
};