/**
 * api.ts — WMS API Service
 *
 * Single function queryWMS() returns WMSResponse.
 * Call buildTabResults() after to populate candidates/resultsByIntent for the UI.
 */

import type { WMSResponse } from "@/types";
import { buildTabResults } from "./buildTabResults";
import { MOCK_RESPONSE } from "@/data/mockResponse";

const BASE_URL = "";
const MOCK_DELAY_MS = 900;
const USE_MOCK = false; // ← flip to true to use mock data

// ─── Real API ─────────────────────────────────────────────────────────────────

async function _fetchFromBackend(
  query: string,
  params?: Record<string, unknown>
): Promise<WMSResponse> {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, params }),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  return res.json() as Promise<WMSResponse>;
}

// ─── Mock API ─────────────────────────────────────────────────────────────────

function _mockFetch(query: string): Promise<WMSResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ ...MOCK_RESPONSE, query });
    }, MOCK_DELAY_MS);
  });
}

// ─── Public ───────────────────────────────────────────────────────────────────

export async function queryWMS(
  query: string,
  params?: Record<string, unknown>
): Promise<WMSResponse> {
  const raw = USE_MOCK
    ? await _mockFetch(query)
    : await _fetchFromBackend(query, params);

  // Derive candidates / selectedIntent / resultsByIntent for UI tabs
  return buildTabResults(raw);
}