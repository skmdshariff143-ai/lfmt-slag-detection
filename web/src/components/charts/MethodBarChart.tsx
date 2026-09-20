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
import { MethodSummary } from "@/types/research";
import { METHOD_COLORS } from "@/lib/data";

interface MethodBarChartProps {
  data: MethodSummary[];
  metricKey: keyof MethodSummary;
  metricLabel: string;
  unit?: string;
  isPercent?: boolean;
}

export const MethodBarChart: React.FC<MethodBarChartProps> = ({
  data,
  metricKey,
  metricLabel,
  unit = "",
  isPercent = false,
}) => {
  const chartData = data.map((d) => {
    const rawVal = d[metricKey];
    const numVal = typeof rawVal === "number" ? rawVal : 0;
    return {
      method: d.method,
      value: isPercent ? Number((numVal * 100).toFixed(1)) : Number(numVal.toFixed(3)),
    };
  });

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 20, left: 10, bottom: 25 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="method"
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#334155" }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#334155" }}
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
            formatter={(val: number) => [`${val}${unit}`, metricLabel]}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={METHOD_COLORS[entry.method] || "#38bdf8"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};