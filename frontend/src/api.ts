// Thin client for the Python backend. In development Vite proxies /api to http://localhost:8000.
import type { ActionResult, AsnDetail, Frame, Meta, OrderDetail } from './types';

const BASE = (import.meta as any).env?.VITE_API_BASE ?? '';

export class ApiError extends Error {}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try { const j = await r.json(); if (j && j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail); } catch { /* not JSON */ }
    throw new ApiError(msg);
  }
  return r.json() as Promise<T>;
}

const qs = (o: Record<string, unknown>) =>
  Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== '').map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');

export interface FrameQuery {
  t: number; at: number | null; role: string; view: string;
  obBy?: string; obSel?: string | null; obCap?: number; arSel?: string | null; traceQ?: string; trWk?: boolean; wi?: number;
  tlPast?: string; tlNext?: string;
}

export const api = {
  meta: () => req<Meta>('/api/meta'),
  frame: (q: FrameQuery, signal?: AbortSignal) => req<Frame>(`/api/frame?${qs({ ...q })}`, { signal }),
  order: (i: number, t: number, at: number | null, role: string) => req<OrderDetail>(`/api/order/${i}?${qs({ t, at, role })}`),
  asn: (i: number, t: number, at: number | null, role: string) => req<AsnDetail>(`/api/asn/${i}?${qs({ t, at, role })}`),
  lookup: (q: string) => req<{ kind: 'order' | 'asn' | null; i?: number; msg?: string }>(`/api/lookup?${qs({ q })}`),
  whatif: (wi: number) => req<any>(`/api/whatif?wi=${wi}`),
  act: (name: string, body: Record<string, unknown>) => req<ActionResult>(`/api/actions/${name}`, { method: 'POST', body: JSON.stringify(body) }),
  login: (name: string, password: string) => req<{ name: string; role: string }>('/api/login', { method: 'POST', body: JSON.stringify({ name, password }) }),
};
