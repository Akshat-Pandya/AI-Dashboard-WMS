/**
 * API Service — WMS Generative UI Dashboard
 *
 * To connect to the real backend:
 *   1. Set VITE_API_BASE_URL in your .env file
 *   2. Change `useMock` to `false` below
 */

import type { QueryResponse } from "@/types";
import { MOCK_QUERY_RESPONSE } from "@/data/mockResponse";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const MOCK_DELAY_MS = 900;

// ─── Real API ─────────────────────────────────────────────────────────────────

async function _fetchFromBackend(
  query: string,
  params?: Record<string, unknown>
): Promise<QueryResponse> {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, params }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  return res.json() as Promise<QueryResponse>;
}

// ─── Mock API ─────────────────────────────────────────────────────────────────

function _mockFetch(query: string): Promise<QueryResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ ...MOCK_QUERY_RESPONSE, query });
    }, MOCK_DELAY_MS);
  });
}

// ─── Public API ───────────────────────────────────────────────────────────────

export async function queryWMS(
  query: string,
  params?: Record<string, unknown>
): Promise<QueryResponse> {
  const useMock = false; // ← flip to true to use mock data

  if (useMock) {
    return _mockFetch(query);
  }

  return _fetchFromBackend(query, params);
}