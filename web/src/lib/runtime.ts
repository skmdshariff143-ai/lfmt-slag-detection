/**
 * Centralized runtime environment and API backend configuration detection.
 */

export type ApiRuntimeMode = "LOCAL_LIVE" | "REMOTE_LIVE" | "HOSTED_OFFLINE";

export function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function isLocalRuntime(): boolean {
  if (!isBrowser()) {
    // In build/SSR, check environment variable
    return process.env.NODE_ENV === "development" || !process.env.VERCEL;
  }
  const hostname = window.location.hostname;
  return (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "0.0.0.0" ||
    hostname.endsWith(".local")
  );
}

export function isHostedRuntime(): boolean {
  return !isLocalRuntime();
}

export function hasConfiguredApiBackend(): boolean {
  const url = process.env.NEXT_PUBLIC_API_BASE_URL;
  return typeof url === "string" && url.trim().length > 0;
}

export function getApiRuntimeStatus(): ApiRuntimeMode {
  if (hasConfiguredApiBackend()) {
    const url = process.env.NEXT_PUBLIC_API_BASE_URL!.trim();
    if (url.includes("localhost") || url.includes("127.0.0.1")) {
      return isLocalRuntime() ? "LOCAL_LIVE" : "HOSTED_OFFLINE";
    }
    return "REMOTE_LIVE";
  }

  if (isLocalRuntime()) {
    return "LOCAL_LIVE";
  }

  return "HOSTED_OFFLINE";
}

export function getApiBaseUrl(): string | null {
  const status = getApiRuntimeStatus();
  if (status === "LOCAL_LIVE") {
    return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  }
  if (status === "REMOTE_LIVE") {
    return process.env.NEXT_PUBLIC_API_BASE_URL!;
  }
  return null; // Hosted offline: no live backend available by design
}
