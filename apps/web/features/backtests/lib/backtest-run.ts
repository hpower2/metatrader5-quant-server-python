import type { BacktestRunResponse } from "@/types/api";
import type { BacktestFormValues, BacktestRunRequest } from "@/features/backtests/schemas/backtest-form";

export function toBacktestRunRequest(values: BacktestFormValues): BacktestRunRequest {
  return {
    symbol: values.symbol,
    timeframe: values.timeframe,
    dataset_name: values.dataset_name,
    dataset_split: values.dataset_split,
    fast_window: values.fast_window,
    slow_window: values.slow_window,
    config: {
      strategy_name: `${values.symbol.toLowerCase()}_${values.timeframe.toLowerCase()}_${values.fast_window}_${values.slow_window}`,
      signal_column: "signal",
      initial_cash: values.initial_cash,
      fee_bps: values.fee_bps,
      slippage_bps: values.slippage_bps,
      fixed_quantity: values.fixed_quantity
    }
  };
}

export function toBacktestMetricsRows(result?: BacktestRunResponse | null) {
  return Object.entries(result?.metrics ?? {}).map(([metric, value]) => ({
    metric,
    value
  }));
}

export function toBacktestParameterRows(values: BacktestFormValues, result?: BacktestRunResponse | null) {
  const sourceMode = result?.data_source?.mode ?? (values.dataset_name ? "dataset" : "warehouse");
  const sourceLabel = sourceMode === "dataset"
    ? `${result?.data_source?.dataset_name ?? values.dataset_name ?? "unknown"} / ${result?.data_source?.dataset_split ?? values.dataset_split}`
    : "warehouse candles";

  return [
    { label: "Strategy", value: result?.config.strategy_name ?? `${values.symbol} crossover` },
    { label: "Signal column", value: result?.config.signal_column ?? "signal" },
    { label: "Data source", value: sourceLabel },
    { label: "Fast / Slow", value: `${values.fast_window} / ${values.slow_window}` },
    { label: "Initial cash", value: values.initial_cash },
    { label: "Fee / Slippage bps", value: `${values.fee_bps} / ${values.slippage_bps}` },
    { label: "Fixed quantity", value: values.fixed_quantity },
    { label: "Artifact dir", value: result?.artifact_dir ?? "Pending run" }
  ];
}

export function toDrawdownSeries(result?: BacktestRunResponse | null) {
  const equityCurve = result?.equity_curve ?? [];
  let rollingMax = Number.NEGATIVE_INFINITY;

  return equityCurve.map((row) => {
    rollingMax = Math.max(rollingMax, row.equity);
    const drawdown = rollingMax > 0 ? (row.equity - rollingMax) / rollingMax : 0;

    return {
      timestamp: row.timestamp,
      drawdown
    };
  });
}
