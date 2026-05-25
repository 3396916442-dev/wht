// =====================================================================
// 与后端 schema 一一对应的全量 API 类型。
// 后端任何字段变化应同步在此处。
// =====================================================================

// ---- 健康 / 元信息 ---------------------------------------------------

export interface ApiHealth {
  status: string;
  version?: string;
  checks?: { mysql: boolean; redis: boolean };
}

export interface ApiRoot {
  name: string;
  version: string;
  docs: string;
  api: string;
}

// ---- 日线 ------------------------------------------------------------

export interface DailyBarItem {
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  pct_change: number | null;
  // 当 indicators=true 时附带：
  ma5?: number | null;
  ma10?: number | null;
  ma20?: number | null;
  ma60?: number | null;
  rsi14?: number | null;
  macd_dif?: number | null;
  macd_dea?: number | null;
  macd_hist?: number | null;
}

export interface DailyResponse {
  stock_code: string;
  start_date: string | null;
  end_date: string | null;
  indicators: boolean;
  count: number;
  items: DailyBarItem[];
}

// ---- 数据同步 --------------------------------------------------------

export interface SyncDailyRequest {
  stock_code: string;
  start_date: string;
  end_date: string;
  adjust?: "" | "qfq" | "hfq";
}

export interface SyncDailyResponse {
  stock_code: string;
  start_date: string;
  end_date: string;
  fetched: number;
  saved: { total: number; affected: number };
}

// ---- 回测 ------------------------------------------------------------

export interface MaCrossRequest {
  stock_code: string;
  start_date: string;
  end_date: string;
  initial_cash?: number;
  short_window?: number;
  long_window?: number;
  commission_rate?: number;
  stamp_tax_rate?: number;
  slippage_rate?: number;
}

export interface BacktestMetrics {
  total_return: number | null;
  annual_return: number | null;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  win_rate: number | null;
  trade_count: number;
}

export interface BacktestTrade {
  trade_date: string;
  action: "BUY" | "SELL";
  price: number;
  quantity: number;
  cash_after: number;
  position_after: number;
  reason: string | null;
}

export interface EquityPoint {
  trade_date: string;
  cash: number;
  position: number;
  close: number;
  equity: number;
}

export interface BacktestDetailResponse {
  task_id: number;
  status: string;
  stock_code: string;
  start_date: string;
  end_date: string;
  initial_cash: number;
  params: { short_window?: number; long_window?: number } & Record<string, unknown>;
  metrics: BacktestMetrics;
  trades: BacktestTrade[];
  equity_curve: EquityPoint[];
}

export interface BacktestTaskListItem {
  task_id: number;
  status: string;
  stock_code: string;
  start_date: string;
  end_date: string;
  created_at: string;
  total_return: number | null;
  trade_count: number;
}

export interface BacktestTaskListResponse {
  count: number;
  items: BacktestTaskListItem[];
}

// ---- AI 报告 ---------------------------------------------------------

export type ReportLevel = "info" | "good" | "warning" | "danger";

export interface ReportSection {
  title: string;
  level: ReportLevel;
  content: string[];
}

export interface BacktestReport {
  task_id: number;
  stock_code: string;
  params: Record<string, unknown>;
  summary: string;
  sections: ReportSection[];
  disclaimer: string;
  generated_at: string;
  provider: string;
}
