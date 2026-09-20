"use client";
import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { SensitivityRecord } from "@/types/research";

interface SensitivityBarChartProps {
  data: SensitivityRecord[];
}

export const SensitivityBarChart: React.FC<SensitivityBarChartProps> = ({ data }) => {
  const chartData = data.map((d) => ({
    variation: d.variation,
    temp_rise_k: d.peak_surface_temp_rise_k,
    defect_contrast_k: Number((d.peak_defect_thermal_contrast_k * 10).toFixed(3)), // scaled for visibility or raw
    pct_cnr: d.pct_cnr,
  }));

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 10, right: 30, left: 140, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            label={{ value: "Peak Surface Temp Rise [K]", position: "insideBottom", offset: -10, fill: "#94a3b8", fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="variation"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "0.375rem",
              color: "#f8fafc",
              fontSize: "12px",
            }}
            formatter={(val: number) => [`${val} K`, "Peak Surface Temp Rise"]}
          />
          <Bar dataKey="temp_rise_k" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.variation === "Baseline" ? "#38bdf8" : "#34d399"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};