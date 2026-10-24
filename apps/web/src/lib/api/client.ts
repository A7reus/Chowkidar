import { getApiToken } from "./token";

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

type QueryPrimitive = string | number | boolean | null | undefined;
type QueryValue = QueryPrimitive | QueryPrimitive[];

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function buildUrl(path: string, params?: Record<string, QueryValue>) {
  const url = new URL(path.startsWith("http") ? path : `${API_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value == null || value === "") continue;
      if (Array.isArray(value)) {
        for (const item of value) {
          if (item != null && item !== "") url.searchParams.append(key, String(item));
        }
      } else {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

function detailMessage(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String(item.msg);
        return null;
      })
      .filter(Boolean);
    return messages.length ? messages.join("; ") : null;
  }
  if (detail && typeof detail === "object" && "detail" in detail) {
    return detailMessage((detail as { detail: unknown }).detail);
  }
  return null;
}

export interface ApiRequestInit extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, QueryValue>;
}

export async function apiFetch<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const { body, params, headers, ...rest } = init;
  const token = getApiToken();
  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "application/json");
  if (token) requestHeaders.set("Authorization", `Bearer ${token}`);
  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, params), {
      ...rest,
      headers: requestHeaders,
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "Could not reach the Chowkidar API.");
  }

  const isAuthAttempt =
    path.startsWith("/api/v1/auth/login") ||
    path.startsWith("/api/v1/auth/refresh") ||
    path.startsWith("/api/v1/auth/demo-login");
  if (response.status === 401 && typeof window !== "undefined" && !isAuthAttempt) {
    window.dispatchEvent(new CustomEvent("chowkidar:unauthorized"));
  }

  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      detail = null;
    }
    const message =
      detailMessage(detail) ??
      (response.status === 403
        ? "Your role does not have access to this action."
        : response.status === 404
          ? "Record not found."
          : "The request failed.");
    throw new ApiError(response.status, message, detail);
  }

  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as T;
  }
  return (await response.json()) as T;
}

export interface DownloadedFile {
  blob: Blob;
  filename: string;
  contentType: string;
}

export async function apiDownload(path: string, fallbackFilename = "report"): Promise<DownloadedFile> {
  const token = getApiToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(buildUrl(path), { headers });
  } catch {
    throw new ApiError(0, "Could not reach the Chowkidar API.");
  }
  if (!response.ok) {
    throw new ApiError(response.status, "Download failed.");
  }
  const disposition = response.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
  const filename = match ? decodeURIComponent(match[1]) : fallbackFilename;
  return {
    blob: await response.blob(),
    filename,
    contentType: response.headers.get("content-type") ?? "application/octet-stream",
  };
}

export function apiUrl(path: string) {
  return buildUrl(path);
}
