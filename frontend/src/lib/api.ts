import { getAccessToken } from "@/lib/auth";
import type { ApiResponse } from "@/lib/types";

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || DEFAULT_API_URL;
}

export class ApiClientError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  auth?: boolean;
};

async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = false } = options;
  const url = `${getApiBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  if (auth) {
    const token = getAccessToken();
    if (!token) {
      throw new ApiClientError("UNAUTHORIZED", "Not authenticated", 401);
    }
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });

  let payload: ApiResponse<T>;
  try {
    payload = (await response.json()) as ApiResponse<T>;
  } catch {
    throw new ApiClientError(
      "INTERNAL_ERROR",
      "Invalid JSON response from API",
      response.status,
    );
  }

  if (!response.ok || !payload.success) {
    throw new ApiClientError(
      payload.error?.code ?? "INTERNAL_ERROR",
      payload.error?.message ?? "Request failed",
      response.status,
    );
  }

  return payload.data as T;
}

export async function apiGet<T>(path: string, auth = false): Promise<T> {
  return apiRequest<T>(path, { method: "GET", auth });
}

export async function apiPost<T>(path: string, body: unknown, auth = false): Promise<T> {
  return apiRequest<T>(path, { method: "POST", body, auth });
}

export async function apiPut<T>(path: string, body: unknown, auth = false): Promise<T> {
  return apiRequest<T>(path, { method: "PUT", body, auth });
}

export async function apiDelete<T = null>(path: string, auth = false): Promise<T> {
  return apiRequest<T>(path, { method: "DELETE", auth });
}
