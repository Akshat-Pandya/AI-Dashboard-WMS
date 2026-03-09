/**
 * buildTabResults.ts
 * Derives per-intent tab results from a WMSResponse.
 */

import type { WMSResponse, IntentTabResult, CandidateIntent, WidgetConfig } from "@/types";

const INTENT_TOOL_LABELS: Record<string, string[]> = {
  warehouse_alerts:        ["get_alerts"],
  low_stock:               ["get_low_stock_items"],
  inventory_lookup:        ["get_inventory_lookup"],
  zone_inventory_compare:  ["compare_zones"],
  order_status:            ["get_order_status"],
  orders_stuck:            ["get_stuck_orders"],
  active_tasks:            ["get_active_tasks"],
  blocked_tasks:           ["get_blocked_tasks"],
  inbound_activity:        ["get_inbound_activity"],
  overdue_asn:             ["get_overdue_asn"],
  kpi_summary:             ["get_kpis"],
  warehouse_overview:      ["get_overview"],
};

// Primary tool_outputs key for each intent
const INTENT_DATA_KEY: Record<string, string> = {
  warehouse_alerts:        "alerts",
  low_stock:               "low_stock",
  inventory_lookup:        "inventory",
  zone_inventory_compare:  "zone_comparison",
  order_status:            "orders",
  orders_stuck:            "stuck_orders",
  active_tasks:            "active_tasks",
  blocked_tasks:           "blocked_tasks",
  inbound_activity:        "inbound",
  overdue_asn:             "overdue_asn",
  kpi_summary:             "kpis",
  warehouse_overview:      "overview",
};

// Maps intent → key inside tool_outputs["trend"] (only for trend-capable intents)
const INTENT_TREND_KEY: Record<string, string> = {
  warehouse_alerts: "alerts",
  inbound_activity: "inbound",
  order_status:     "orders",
  active_tasks:     "active_tasks",
  blocked_tasks:    "blocked_tasks",
};

/** Deduplicate widgets — keep only the first widget per data_key. */
function dedupeWidgets(widgets: WidgetConfig[]): WidgetConfig[] {
  const seen = new Set<string>();
  return widgets.filter((w) => {
    if (seen.has(w.data_key)) return false;
    seen.add(w.data_key);
    return true;
  });
}

/**
 * Decide if a widget belongs to a given intent.
 *
 * Rules:
 *  1. Trend widget ("trend.inbound") → belongs if trendKey matches
 *  2. Primary key prefix ("inbound", "inbound.asns") → belongs to intent
 */
function widgetBelongsToIntent(
  widget: WidgetConfig,
  primaryKey: string,
  trendKey: string | undefined,
): boolean {
  const dk = widget.data_key;

  // Trend widget e.g. "trend.inbound"
  if (dk.startsWith("trend.") && trendKey) {
    return dk === `trend.${trendKey}`;
  }

  // Primary key prefix match e.g. "inbound" matches "inbound.asns"
  if (primaryKey && dk.startsWith(primaryKey)) return true;

  return false;
}

export function buildTabResults(raw: WMSResponse): WMSResponse {
  const sorted = [...(raw.intents ?? [])].sort((a, b) => b.confidence - a.confidence);

  const candidates: CandidateIntent[] = sorted.map((s) => ({
    name:       s.intent,
    confidence: s.confidence,
  }));

  const selectedIntent = sorted[0]?.intent ?? "unknown";

  // Dedupe the raw widget list once
  const dedupedWidgets = dedupeWidgets(raw.widgets ?? []);

  const resultsByIntent: IntentTabResult[] = sorted.map((s) => {
    const primaryKey = INTENT_DATA_KEY[s.intent] ?? "";
    const trendKey   = INTENT_TREND_KEY[s.intent];

    // ── Widgets for this intent ───────────────────────────────────────────────
    const intentWidgets: WidgetConfig[] = dedupedWidgets.filter((w) =>
      widgetBelongsToIntent(w, primaryKey, trendKey)
    );

    // ── Data for this intent ──────────────────────────────────────────────────
    const intentData: Record<string, unknown> = {};

    // Primary tool output (e.g. data["inbound"])
    if (primaryKey && raw.data[primaryKey] !== undefined) {
      intentData[primaryKey] = raw.data[primaryKey];
    }

    // Trend data — needed when a LINE_CHART widget with "trend.X" is present.
    // Copy the whole trend object so resolvePath("trend.inbound") works.
    const hasTrendWidget = intentWidgets.some((w) => w.data_key.startsWith("trend."));
    if (hasTrendWidget && raw.data.trend && typeof raw.data.trend === "object") {
      intentData["trend"] = raw.data.trend;
    }

    return {
      intent:        s.intent,
      confidence:    s.confidence,
      toolsExecuted: INTENT_TOOL_LABELS[s.intent] ?? [s.intent],
      summary:       raw.summary ? [raw.summary] : [],
      widgets:       intentWidgets,
      data:          intentData,
    };
  });

  return { ...raw, candidates, selectedIntent, resultsByIntent };
}