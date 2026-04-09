export type StatusTone = "success" | "warning" | "error" | "info" | "neutral";

export interface HealthStatus {
  status: string;
  database: {
    ok: boolean;
    error: string | null;
  };
  mt5: {
    status?: string | undefined;
    mt5_initialized?: boolean | undefined;
    mt5_connected?: boolean | undefined;
    error?: string | undefined;
  } | null;
}

export interface SyncCheckpoint {
  job_type: string;
  symbol: string | null;
  timeframe: string | null;
  last_synced_at: string | null;
  last_ingested_bar_at: string | null;
  last_status: string;
  last_error: string | null;
  cursor: Record<string, unknown>;
}

export interface SymbolSummary {
  symbol: string;
  description: string | null;
  path: string | null;
  visible: boolean;
  digits: number | null;
  trade_mode: number | null;
}

export interface CandleRecord {
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  tick_volume: number;
  real_volume: number;
  spread: number;
  quality_flags: string[];
}

export interface FeatureRunResponse {
  rows: number;
  columns: string[];
  artifact_path: string;
}

export interface DatasetBuildResponse {
  artifact_dir: string;
  dataset_rows: number;
  train_rows: number;
  validation_rows: number;
  test_rows: number;
  walk_forward_slices: Array<Record<string, number>>;
}

export interface BacktestRunResponse {
  artifact_dir: string;
  config: {
    strategy_name: string;
    signal_column: string;
    initial_cash: number;
    fee_bps: number;
    slippage_bps: number;
    fixed_quantity: number;
    risk_per_trade?: number | null | undefined;
    stop_loss_pct?: number | null | undefined;
    take_profit_pct?: number | null | undefined;
  };
  data_source?: {
    mode: "warehouse" | "dataset";
    dataset_name: string | null;
    dataset_split: "train" | "validation" | "test" | null;
  } | undefined;
  metrics: Record<string, number>;
  trade_count: number;
  equity_rows: number;
  equity_curve: Array<{
    timestamp: string;
    equity: number;
  }>;
  trades: Array<{
    entry_time: string;
    exit_time: string;
    side: number;
    quantity: number;
    entry_price: number;
    exit_price: number;
    pnl: number;
  }>;
}

export interface PaperAccountStatus {
  account: {
    name: string;
    currency: string;
    cash: number;
    equity: number;
    status: string;
    last_mark_to_market_at: string | null;
  };
  open_positions: Array<{
    id: string;
    symbol: string;
    side: string;
    quantity: number;
    entry_price: number;
    current_price: number;
    realized_pnl: number;
    unrealized_pnl: number;
    opened_at: string;
  }>;
  recent_fills: Array<{
    id: string;
    symbol: string;
    side: string;
    quantity: number;
    price: number;
    event_time: string;
  }>;
}
