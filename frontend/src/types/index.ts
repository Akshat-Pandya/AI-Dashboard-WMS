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

export interface WidgetConfig {
  type: WidgetType | string;
  title: string;
  data_key: string;
  props?: Record<string, unknown>;
}

// ─── Intent ───────────────────────────────────────────────────────────────────

export interface IntentScore {
  intent: string;
  confidence: number;
}

// ─── Per-intent tab result ────────────────────────────────────────────────────

export interface IntentTabResult {
  intent: string;
  confidence: number;
  toolsExecuted: string[];
  summary: string[];
  widgets: WidgetConfig[];
  data: Record<string, unknown>;
}

// ─── Single unified API response type ────────────────────────────────────────
// This is what the backend returns AND what all UI components consume.
// No more ChatResponse / QueryResponse split.

export interface WMSResponse {
  query: string;
  summary: string;
  intents: IntentScore[];
  widgets: WidgetConfig[];
  data: Record<string, unknown>;
  // Derived fields — built client-side from intents (see buildTabResults)
  candidates?: CandidateIntent[];
  selectedIntent?: string;
  resultsByIntent?: IntentTabResult[];
}

// ─── Candidate intent (for AllIntentsPanel display) ───────────────────────────

export interface CandidateIntent {
  name: string;
  confidence: number;
}

// ─── Chat history ─────────────────────────────────────────────────────────────

export interface ChatHistoryItem {
  query: string;
  timestamp: number;
}

// ─── Widget payload shapes ────────────────────────────────────────────────────

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
  cards?: KPICard[];
  kpis?: KPICard[];
}

export interface TableData {
  columns: string[];
  rows: (string | number)[][];
}

export interface BarChartData {
  bars: Record<string, unknown>[];
  keys: string[];
  colors: string[];
}

export interface LineChartData {
  points: Record<string, string | number>[];
  keys: string[];
  colors?: string[];
}

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

export type WidgetData =
  | KPICardsData
  | TableData
  | BarChartData
  | LineChartData
  | AlertListData
  | ZoneCompareData;

// ─── Legacy WidgetSpec (old mock-based components) ────────────────────────────

export interface WidgetSpec {
  type: WidgetType;
  title: string;
  data: WidgetData;
}

// ─── Deprecated aliases — remove once all components use WMSResponse ──────────

/** @deprecated Use WMSResponse */
export type QueryResponse = WMSResponse;

/** @deprecated Use WMSResponse */
export type ChatResponse = WMSResponse;