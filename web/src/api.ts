import type { ScreeningDetail, ScreeningItem, Stage } from "./types";

const API_BASE =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") ??
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export function fetchScreenings(): Promise<ScreeningItem[]> {
  return request<ScreeningItem[]>("/screenings?limit=100");
}

export function fetchScreening(id: string): Promise<ScreeningDetail> {
  return request<ScreeningDetail>(`/screenings/${id}`);
}

export function updateStage(id: string, stage: Stage): Promise<ScreeningDetail> {
  return request<ScreeningDetail>(`/screenings/${id}/stage`, {
    method: "PATCH",
    body: JSON.stringify({ stage }),
  });
}
