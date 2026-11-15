// The API is the only thing the frontend talks to (README 3, rule 1).
// VITE_USE_FIXTURES=true reads mock_data/astro/ directly (works with the backend down).
// The dev server needs in vite.config.ts:  server: { fs: { allow: [".."] } }
import { FixtureMissingError, resolveFixture, type FixtureFiles } from "./fixtures";

const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
export const API_PREFIX = "/api";
export const USE_FIXTURES: boolean = import.meta.env.VITE_USE_FIXTURES === "true";

const fixtureFiles = (
  USE_FIXTURES ? import.meta.glob("../../../mock_data/astro/**/*.json", { query: "?raw", import: "default" }) : {}
) as FixtureFiles;

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

type Params = Record<string, string | number | undefined>;

async function fromFixtures<T>(method: "GET" | "POST", path: string, params?: Params, body?: unknown): Promise<T> {
  try {
    return await resolveFixture<T>(fixtureFiles, method, path, params, body);
  } catch (e) {
    if (e instanceof FixtureMissingError) throw new ApiError(404, "FIXTURE_MISSING", e.message);
    throw e;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${API_PREFIX}${path}`, init);
  const body = await res.json().catch(() => null);
  // P3 errors come back as HTTP 422 with { error: { code, message } }.
  if (!res.ok || body?.status === "error") {
    const e = body?.error;
    throw new ApiError(res.status, e?.code ?? "HTTP_ERROR", e?.message ?? res.statusText);
  }
  return body as T;
}

export const apiGet = <T>(path: string, params?: Params): Promise<T> => {
  if (USE_FIXTURES) return fromFixtures<T>("GET", path, params);
  const q = params
    ? "?" +
      Object.entries(params)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join("&")
    : "";
  return request<T>(`${path}${q}`);
};

export const apiPost = <T>(path: string, body: unknown): Promise<T> => {
  if (USE_FIXTURES) return fromFixtures<T>("POST", path, undefined, body);
  return request<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
};
