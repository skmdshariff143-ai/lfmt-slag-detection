export { METHOD_COLORS } from "./constants";

export function formatMetric(
  val: number | null | undefined,
  decimals: number = 2,
  unit: string = ""
): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "N/A";
  }
  return `${val.toFixed(decimals)}${unit ? " " + unit : ""}`;
}

export function formatPct(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) {
    return "N/A";
  }
  const num = val <= 1.0 ? val * 100 : val;
  return `${num.toFixed(1)}%`;
}
