import {
  ResearchManifest,
  MethodSummary,
  DepthSummary,
  DiameterSummary,
  NoiseSummary,
  HealthySummary,
  MaxDepthRecord,
  SensitivityRecord,
  CaseManifest,
  CaseIndexItem,
} from "@/types/research";

import manifestData from "../../public/data/manifest.json";
import summaryMethodData from "../../public/data/summary_by_method.json";
import summaryDepthData from "../../public/data/summary_by_depth.json";
import summaryDiameterData from "../../public/data/summary_by_diameter.json";
import summaryNoiseData from "../../public/data/summary_by_noise.json";
import healthyData from "../../public/data/healthy_specificity.json";
import maxDepthData from "../../public/data/max_detectable_depth.json";
import sensitivityData from "../../public/data/sensitivity_summary.json";
import caseIndexData from "../../public/cases/index.json";

// Case-specific static manifests
import caseD040_Z002 from "../../public/cases/D040_Z002.json";
import caseD060_Z004 from "../../public/cases/D060_Z004.json";
import caseD080_Z004 from "../../public/cases/D080_Z004.json";
import caseD100_Z006 from "../../public/cases/D100_Z006.json";
import caseD120_Z008 from "../../public/cases/D120_Z008.json";
import caseHEALTHY from "../../public/cases/HEALTHY_CONTROL.json";

export { METHOD_COLORS, formatMetric, formatPct } from "./format";

const CASE_REGISTRY: Record<string, CaseManifest> = {
  D040_Z002: caseD040_Z002 as unknown as CaseManifest,
  D060_Z004: caseD060_Z004 as unknown as CaseManifest,
  D080_Z004: caseD080_Z004 as unknown as CaseManifest,
  D100_Z006: caseD100_Z006 as unknown as CaseManifest,
  D120_Z008: caseD120_Z008 as unknown as CaseManifest,
  HEALTHY_CONTROL: caseHEALTHY as unknown as CaseManifest,
};

function sanitizeNull(val: unknown): number | null {
  if (val === null || val === undefined || (typeof val === "number" && isNaN(val))) {
    return null;
  }
  return Number(val);
}

export function getManifest(): ResearchManifest {
  return manifestData as unknown as ResearchManifest;
}

export function getMethodSummaries(): MethodSummary[] {
  return (summaryMethodData as unknown as MethodSummary[]).map((s) => ({
    ...s,
    mean_loc_error_detected_mm: sanitizeNull(s.mean_loc_error_detected_mm),
    mean_loc_error_mm: sanitizeNull(s.mean_loc_error_mm),
  }));
}

export function getDepthSummaries(): DepthSummary[] {
  return (summaryDepthData as unknown as DepthSummary[]).map((d) => ({
    ...d,
    mean_loc_error_detected_mm: sanitizeNull(d.mean_loc_error_detected_mm),
    mean_loc_error_mm: sanitizeNull(d.mean_loc_error_mm),
  }));
}

export function getDiameterSummaries(): DiameterSummary[] {
  return (summaryDiameterData as unknown as DiameterSummary[]).map((d) => ({
    ...d,
    mean_loc_error_detected_mm: sanitizeNull(d.mean_loc_error_detected_mm),
    mean_loc_error_mm: sanitizeNull(d.mean_loc_error_mm),
  }));
}

export function getNoiseSummaries(): NoiseSummary[] {
  return (summaryNoiseData as unknown as NoiseSummary[]).map((n) => ({
    ...n,
    mean_loc_error_detected_mm: sanitizeNull(n.mean_loc_error_detected_mm),
    mean_loc_error_mm: sanitizeNull(n.mean_loc_error_mm),
  }));
}

export function getHealthySummaries(): HealthySummary[] {
  return healthyData as unknown as HealthySummary[];
}

export function getMaxDepthRecords(): MaxDepthRecord[] {
  return maxDepthData as unknown as MaxDepthRecord[];
}

export function getSensitivityRecords(): SensitivityRecord[] {
  return (sensitivityData as unknown as SensitivityRecord[]).map((r) => ({
    ...r,
    pct_loc_error_mm: sanitizeNull(r.pct_loc_error_mm),
  }));
}

export function getCaseIndex(): CaseIndexItem[] {
  return caseIndexData as unknown as CaseIndexItem[];
}

export function getCaseManifest(caseTag: string): CaseManifest | null {
  return CASE_REGISTRY[caseTag] || null;
}