import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import { ProvenanceBanner } from "@/components/ProvenanceBanner";
import { Footer } from "@/components/Footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "LFMT Subsurface Slag Detection | Computational NDT Research",
  description:
    "Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion Detection in Mild Steel: 3D FEM Simulation, Pulse Compression, PCT, SPCT, and RPT Benchmark.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable} dark`}>
      <body className="min-h-screen flex flex-col bg-slate-950 text-slate-100 antialiased font-sans">
        <ProvenanceBanner />
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}