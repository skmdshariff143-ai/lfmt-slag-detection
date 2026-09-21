/**
 * Canonical REST API Client for LFMT Intelligent Defect Analyzer Backend.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface ExampleCardInfo {
  id: string;
  title: string;
  short_description: string;
  category: string;
  source_type: string;
  material: string;
  excitation_type: string;
  defect_description: string;
  frames: number;
  resolution: [number, number];
  frame_rate_hz: number;
  duration_s: number;
  temperature_unit_status: string;
  radiometric_status: string;
  fov_status: string;
  GT_available: boolean;
  example_available: boolean;
  supported_methods: string[];
}

export async function fetchVerifiedExamples(): Promise<ExampleCardInfo[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/examples`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch examples: HTTP ${res.status}`);
  }
  return res.json();
}

export async function runExampleAnalysis(
  exampleId: string,
  applyBaseline = true,
  smoothSigma = 0.0
): Promise<any> {
  const url = `${API_BASE_URL}/api/v1/examples/${encodeURIComponent(
    exampleId
  )}/analyze?apply_baseline=${applyBaseline}&smooth_sigma_px=${smoothSigma}`;
  const res = await fetch(url, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Analysis failed with status ${res.status}`);
  }
  return res.json();
}

export async function uploadAndAnalyzeFile(formData: FormData): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/analyze/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Upload failed with status ${res.status}`);
  }
  return res.json();
}
