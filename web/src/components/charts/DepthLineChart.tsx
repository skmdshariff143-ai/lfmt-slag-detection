"use client";
import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { DepthSummary } from "@/types/research";
import { METHOD_COLORS } from "@/lib/data";

interface DepthLineChartProps {
  data: DepthSummary[];
  metricKey: "detection_rate" | "mean_cnr" | "mean_iou" | "mean_loc_error_detected_mm";
  metricLabel: string;
  unit?: string;
  isPercent?: boolean;
}

export const DepthLineChart: React.FC<DepthLineChartProps> = ({
  data,
  metricKey,
  metricLabel,
  unit = "",
  isPercent = false,
}) => {
  const depths = Array.from(new Set(data.map((d) => d.depth_mm))).sort((a, b) => a - b);
  const methods = Array.from(new Set(data.map((d) => d.method)));

  const chartData = depths.map((z) => {
    const row: Record<string, number | null> = { depth_mm: z };
    methods.forEach((m) => {
      const match = data.find((d) => d.depth_mm === z && d.method === m);
      if (match && match[metricKey] !== null && match[metricKey] !== undefined) {
        const val = Number(match[metricKey]);
        row[m] = isPercent ? Number((val * 100).toFixed(1)) : Number(val.toFixed(3));
      } else {
        row[m] = null;
      }
    });
    return row;
  });

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="depth_mm"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            label={{ value: "Inclusion Depth z [mm]", position: "insideBottom", offset: -10, fill: "#94a3b8", fontSize: 12 }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            unit={unit}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0f172a",
              borderColor: "#334155",
              borderRadius: "0.375rem",
              color: "#f8fafc",
              fontSize: "12px",
            }}
          />
          <Legend
            verticalAlign="top"
            wrapperStyle={{ paddingBottom: "10px", fontSize: "12px" }}
          />
          {methods.map((m) => (
            <Line
              key={m}
              type="monotone"
              dataKey={m}
              stroke={METHOD_COLORS[m] || "#38bdf8"}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};