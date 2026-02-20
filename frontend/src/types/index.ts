// ─── Widget Types ─────────────────────────────────────────────────────────────

export type WidgetType =
  | "KPI_CARDS"
  | "TABLE"
  | "BAR_CHART"
  | "LINE_CHART"
  | "ALERT_LIST";

// KPI_CARDS payload
export interface KPICard {
  label: string;
  value: string;
  unit: string;
  trend: string;
  up: boolean;
  icon: string;
}

export interface KPICardsData {
  cards: KPICard[];
}

// TABLE payload
export interface TableData {
  columns: string[];
  rows: (string | number)[][];
}

// BAR_CHART payload
export interface BarChartData {
  bars: Record<string, string | number>[];
  keys: string[];
  colors: string[];
}

// LINE_CHART payload
export interface LineChartData {
  points: Record<string, string | number>[];
  keys: string[];
  colors?: string[];
}

// ALERT_LIST payload
export type AlertSeverity = "CRITICAL" | "HIGH" | "MEDIUM";

export interface Alert {
  id: string;
  severity: AlertSeverity;
  message: string;
  time: string;
}

export interface AlertListData {
  alerts: Alert[];
}

// Union widget payload
export type WidgetData =
  | KPICardsData
  | TableData
  | BarChartData
  | LineChartData
  | AlertListData;

// ─── Core Data Contract ───────────────────────────────────────────────────────

export interface WidgetSpec {
  type: WidgetType;
  title: string;
  data: WidgetData;
}

export interface CandidateIntent {
  name: string;       // e.g. "INVENTORY", "TASKS", "OVERVIEW"
  confidence: number; // 0..1
}

export interface IntentTabResult {
  intent: string;
  confidence: number;
  toolsExecuted: string[];
  summary: string[];
  widgets: WidgetSpec[];
}

export interface ChatResponse {
  query: string;
  candidates: CandidateIntent[];
  selectedIntent: string;
  resultsByIntent: IntentTabResult[];
}

// ─── Chat History ─────────────────────────────────────────────────────────────

export interface ChatHistoryItem {
  query: string;
  timestamp: number;
}
