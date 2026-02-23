/**
 * buildTabResults.ts
 * Derives per-intent tab results from a WMSResponse.
 * Each tab only shows the widget and data slice for its own intent.
 *
 * Place in: src/services/buildTabResults.ts
 */

import type { WMSResponse, IntentTabResult, CandidateIntent, WidgetConfig } from "@/types";

const INTENT_TOOL_LABELS: Record<string, string[]> = {
  warehouse_alerts: ["get_alerts"],
  low_stock: ["get_low_stock_items"],
  inventory_lookup: ["get_inventory_lookup"],
  zone_inventory_compare: ["compare_zones"],
  order_status: ["get_order_status"],
  orders_stuck: ["get_stuck_orders"],
  active_tasks: ["get_active_tasks"],
  blocked_tasks: ["get_blocked_tasks"],
  inbound_activity: ["get_inbound_activity"],
  overdue_asn: ["get_overdue_asn"],
  kpi_summary: ["get_kpis"],
  warehouse_overview: ["get_overview"],
};

// Maps each intent to the top-level data key it owns in response.data
const INTENT_DATA_KEY: Record<string, string> = {
  warehouse_alerts: "alerts",
  low_stock: "low_stock",
  inventory_lookup: "inventory",
  zone_inventory_compare: "zone_comparison",
  order_status: "orders",
  orders_stuck: "stuck_orders",
  active_tasks: "active_tasks",
  blocked_tasks: "blocked_tasks",
  inbound_activity: "inbound",
  overdue_asn: "overdue_asn",
  kpi_summary: "kpis",
  warehouse_overview: "overview",
};

export function buildTabResults(raw: WMSResponse): WMSResponse {
  const sorted = [...(raw.intents ?? [])].sort((a, b) => b.confidence - a.confidence);

  const candidates: CandidateIntent[] = sorted.map((s) => ({
    name: s.intent,
    confidence: s.confidence,
  }));

  const selectedIntent = sorted[0]?.intent ?? "unknown";

  const resultsByIntent: IntentTabResult[] = sorted.map((s) => {
    const dataKey = INTENT_DATA_KEY[s.intent];

    // Only include widgets whose data_key starts with this intent's data key
    const intentWidgets: WidgetConfig[] = raw.widgets.filter((w) =>
      dataKey ? w.data_key.startsWith(dataKey) : false
    );

    // Only include the data slice for this intent
    const intentData: Record<string, unknown> = dataKey && raw.data[dataKey]
      ? { [dataKey]: raw.data[dataKey] }
      : {};

    return {
      intent: s.intent,
      confidence: s.confidence,
      toolsExecuted: INTENT_TOOL_LABELS[s.intent] ?? [s.intent],
      summary: raw.summary ? [raw.summary] : [],
      widgets: intentWidgets,
      data: intentData,
    };
  });

  return { ...raw, candidates, selectedIntent, resultsByIntent };
}