/**
 * Canonical REST API Client for LFMT Intelligent Defect Analyzer Backend.
 * Handles local live execution, remote live execution, and hosted offline modes gracefully.
 */

import {
  getApiBaseUrl,
  getApiRuntimeStatus,
  isLocalRuntime,
  isHostedRuntime,
  ApiRuntimeMode,
} from "./runtime";

export { getApiRuntimeStatus, isLocalRuntime, isHostedRuntime };
export type { ApiRuntimeMode };

export const API_BASE_URL = getApiBaseUrl() || "";

export class BackendOfflineError extends Error {
  constructor(message = "Live analysis/simulation backend is offline in this hosted environment.") {
    super(message);
    this.name = "BackendOfflineError";
  }
}

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
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError();
  }
  const res = await fetch(`${baseUrl}/api/v1/examples`, {
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
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError(
      "LIVE ANALYSIS BACKEND OFFLINE: The Python analysis API is offline in this hosted preview. Run 'scripts/demo/start_local_demo.ps1' to test live analysis locally."
    );
  }
  const url = `${baseUrl}/api/v1/examples/${encodeURIComponent(
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
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError(
      "LIVE ANALYSIS BACKEND OFFLINE: The Python analysis API is offline in this hosted preview. Run 'scripts/demo/start_local_demo.ps1' to test live upload analysis locally."
    );
  }
  const res = await fetch(`${baseUrl}/api/v1/analyze/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Upload failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchSimulationBackends(): Promise<any> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    // In hosted offline mode, return truthful offline status without attempting network call
    return {
      matlab_fdm: {
        status: "UNAVAILABLE",
        engine: "R2026a",
        connection_mode: "offline",
        message: "Unavailable in hosted preview (UNAVAILABLE_BY_DESIGN)",
      },
      python_fem: {
        status: "UNAVAILABLE",
        engine: "scikit-fem",
        message: "Unavailable in hosted preview",
      },
    };
  }
  try {
    const res = await fetch(`${baseUrl}/api/v1/simulate/backends`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
  } catch (e) {
    return {
      matlab_fdm: {
        status: "UNAVAILABLE",
        engine: "R2026a",
        connection_mode: "offline",
        message: "Live MATLAB backend offline",
      },
      python_fem: {
        status: "UNAVAILABLE",
        engine: "scikit-fem",
        message: "Live Python backend offline",
      },
    };
  }
}

export async function startSimulationRun(payload: any): Promise<{ run_id: string; status: string }> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError(
      "LIVE MATLAB BACKEND OFFLINE: Simulation backend is unreachable in this hosted preview."
    );
  }
  const res = await fetch(`${baseUrl}/api/v1/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Simulation dispatch failed with status ${res.status}`);
  }
  return res.json();
}

export async function getSimulationStatus(runId: string): Promise<any> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError();
  }
  const res = await fetch(`${baseUrl}/api/v1/simulate/${encodeURIComponent(runId)}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch simulation status: HTTP ${res.status}`);
  }
  return res.json();
}

export async function getSimulationResult(runId: string): Promise<any> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError();
  }
  const res = await fetch(`${baseUrl}/api/v1/simulate/${encodeURIComponent(runId)}/result`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch simulation result: HTTP ${res.status}`);
  }
  return res.json();
}

export async function compareSimulationBackends(preset: string = "shallow_slag"): Promise<any> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new BackendOfflineError(
      "LIVE BACKEND OFFLINE: Comparison requires active local Python & MATLAB backends."
    );
  }
  const res = await fetch(`${baseUrl}/api/v1/simulate/compare?preset=${encodeURIComponent(preset)}`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to run backend comparison: HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchPrecomputedSimulation(): Promise<any> {
  const baseUrl = getApiBaseUrl();
  if (baseUrl) {
    try {
      const res = await fetch(`${baseUrl}/api/v1/simulate/precomputed`, {
        cache: "no-store",
      });
      if (res.ok) {
        return res.json();
      }
    } catch {
      // Fallback to static asset
    }
  }
  // Static asset fallback for hosted Vercel preview or offline backend
  const staticRes = await fetch("/demo/matlab_shallow_slag.json");
  if (!staticRes.ok) {
    throw new Error(`Failed to load static precomputed demo: HTTP ${staticRes.status}`);
  }
  return staticRes.json();
}
