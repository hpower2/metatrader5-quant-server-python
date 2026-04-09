import { z } from "zod";

const API_BASE_URL = "/api/control";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload?: unknown
  ) {
    super(message);
  }
}

async function parseResponse<T>(response: Response, schema: z.ZodType<T>): Promise<T> {
  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(`API request failed with status ${response.status}`, response.status, data);
  }
  return schema.parse(data);
}

export async function apiGet<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  return parseResponse(response, schema);
}

export async function apiPost<TInput, TOutput>(
  path: string,
  payload: TInput,
  schema: z.ZodType<TOutput>,
  init?: RequestInit
): Promise<TOutput> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    body: JSON.stringify(payload),
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  return parseResponse(response, schema);
}
