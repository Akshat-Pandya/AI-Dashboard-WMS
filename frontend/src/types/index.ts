// ─── Widget Types ─────────────────────────────────────────────────────────────

export type WidgetType =
  | "KPI_CARDS"
  | "TABLE"
  | "BAR_CHART"
  | "LINE_CHART"
  | "ALERT_LIST"
  | "ZONE_COMPARE_CHART"
  | "INBOUND_SUMMARY"
  | "OVERVIEW_PANEL";

// ─── Widget Config (from backend orchestrator) ────────────────────────────────

export interface WidgetConfig {
  type: WidgetType | string; // string fallback for future types
  title: string;
  data_key: string;          // dot-path into QueryResponse.data, e.g. "alerts.alerts"
  props?: Record<string, unknown>;
}

// ─── Top-level API Response ───────────────────────────────────────────────────

export interface QueryResponse {
  query: string;
  summary: string;
  widgets: WidgetConfig[];
  data: Record<string, unknown>;
}

// ─── KPI_CARDS payload ────────────────────────────────────────────────────────

export interface KPICard {
  label: string;
  value: string | number;
  unit?: string;
  trend?: string;
  up?: boolean;
  icon?: string;
  alert?: boolean;
}

export interface KPICardsData {
  cards?: KPICard[]; // frontend shape
  kpis?: KPICard[];  // backend shape (get_kpis returns { kpis: [] })
}

// ─── TABLE payload ────────────────────────────────────────────────────────────

export interface TableData {
  columns: string[];
  rows: (string | number)[][];
}

// ─── BAR_CHART / ZONE_COMPARE_CHART payload ───────────────────────────────────

export interface BarChartData {
  bars: Record<string, unknown>[];
  keys: string[];     // ← required
  colors: string[];   // ← required
}

// ─── LINE_CHART payload ───────────────────────────────────────────────────────

export interface LineChartData {
  points: Record<string, string | number>[];
  keys: string[];
  colors?: string[];
}

// ─── ALERT_LIST payload ───────────────────────────────────────────────────────

export type AlertSeverity = "CRITICAL" | "HIGH" | "MEDIUM";

export interface Alert {
  id: string;
  severity: AlertSeverity;
  title?: string;
  message: string;
  time?: string;
  timestamp?: string;
  category?: string;
  acknowledged?: boolean;
  zone?: string;
}

export interface AlertListData {
  count?: number;
  alerts: Alert[];
}

// ─── Inventory types ──────────────────────────────────────────────────────────

export interface InventoryItem {
  sku: string;
  name: string;
  zone: string;
  quantity: number;
  reorder_point: number;
  unit: string;
}

// ─── Zone comparison ──────────────────────────────────────────────────────────

export interface ZoneRow {
  zone: string;
  total_skus: number;
  total_units: number;
  low_stock_count: number;
  avg_quantity: number;
}

export interface ZoneCompareData {
  zones: ZoneRow[];
}

// ─── Union widget payload ─────────────────────────────────────────────────────

export type WidgetData =
  | KPICardsData
  | TableData
  | BarChartData
  | LineChartData
  | AlertListData
  | ZoneCompareData;

// ─── Chat History ─────────────────────────────────────────────────────────────

export interface ChatHistoryItem {
  query: string;
  timestamp: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// LEGACY — kept for existing UI components (IntentTabs, AllIntentsPanel, etc.)
// These types reflect the old mock-based response shape.
// Once those components are migrated to QueryResponse, these can be removed.
// ─────────────────────────────────────────────────────────────────────────────

export interface WidgetSpec {
  type: WidgetType;
  title: string;
  data: WidgetData;
}

export interface CandidateIntent {
  name: string;
  confidence: number;
}

export interface IntentTabResult {
  intent: string;
  confidence: number;
  toolsExecuted: string[];
  summary: string[];
  widgets: WidgetSpec[];
}

/** @deprecated Use QueryResponse instead. Kept for IntentTabs / AllIntentsPanel compatibility. */
export interface ChatResponse {
  query: string;
  candidates: CandidateIntent[];
  selectedIntent: string;
  resultsByIntent: IntentTabResult[];
}