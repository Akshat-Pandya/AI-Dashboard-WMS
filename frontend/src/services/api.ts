/**
 * API Service — WMS Generative UI Dashboard
 *
 * Currently uses mock data with a simulated latency.
 * To connect to a real backend, replace the `queryWMS` implementation:
 *   - Remove the setTimeout mock block
 *   - Uncomment the fetch() call
 *   - Point BASE_URL to your actual API endpoint
 */

import type { ChatResponse } from "@/types";
import { MOCK_RESPONSE } from "@/data/mockResponse";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
const MOCK_DELAY_MS = 900;

// ─── Real API (swap in when backend is ready) ─────────────────────────────────

async function _fetchFromBackend(query: string): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`API error ${response.status}: ${err}`);
  }

  return response.json() as Promise<ChatResponse>;
}

// ─── Mock API (used by default) ───────────────────────────────────────────────

function _mockFetch(query: string): Promise<ChatResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ ...MOCK_RESPONSE, query });
    }, MOCK_DELAY_MS);
  });
}

// ─── Public API function ──────────────────────────────────────────────────────

/**
 * Send a natural-language query to the WMS backend (or mock).
 *
 * To switch to the real backend:
 *   1. Set VITE_API_BASE_URL in your .env file
 *   2. Change `useMock` to `false` below
 */
export async function queryWMS(query: string): Promise<ChatResponse> {
  const useMock = true; // ← flip to false when real API is available

  if (useMock) {
    return _mockFetch(query);
  }

  return _fetchFromBackend(query);
}
