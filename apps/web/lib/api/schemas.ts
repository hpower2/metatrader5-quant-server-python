import { z } from "zod";

import { candleSchema, healthSchema, symbolSchema, syncCheckpointSchema } from "@/schemas/common";

export const featureRunResponseSchema = z.object({
  rows: z.number(),
  columns: z.array(z.string()),
  artifact_path: z.string()
});

export const datasetBuildResponseSchema = z.object({
  artifact_dir: z.string(),
  dataset_rows: z.number(),
  train_rows: z.number(),
  validation_rows: z.number(),
  test_rows: z.number(),
  walk_forward_slices: z.array(z.record(z.string(), z.number()))
});

export const backtestRunResponseSchema = z.object({
  artifact_dir: z.string(),
  config: z.object({
    strategy_name: z.string(),
    signal_column: z.string(),
    initial_cash: z.number(),
    fee_bps: z.number(),
    slippage_bps: z.number(),
    fixed_quantity: z.number(),
    risk_per_trade: z.number().nullable().optional(),
    stop_loss_pct: z.number().nullable().optional(),
    take_profit_pct: z.number().nullable().optional()
  }),
  data_source: z
    .object({
      mode: z.enum(["warehouse", "dataset"]),
      dataset_name: z.string().nullable(),
      dataset_split: z.enum(["train", "validation", "test"]).nullable()
    })
    .optional(),
  metrics: z.record(z.string(), z.number()),
  trade_count: z.number(),
  equity_rows: z.number(),
  equity_curve: z.array(
    z.object({
      timestamp: z.string(),
      equity: z.number()
    })
  ),
  trades: z.array(
    z.object({
      entry_time: z.string(),
      exit_time: z.string(),
      side: z.number(),
      quantity: z.number(),
      entry_price: z.number(),
      exit_price: z.number(),
      pnl: z.number()
    })
  )
});

export const paperStatusSchema = z.object({
  account: z.object({
    name: z.string(),
    currency: z.string(),
    cash: z.number(),
    equity: z.number(),
    status: z.string(),
    last_mark_to_market_at: z.string().nullable()
  }),
  open_positions: z.array(
    z.object({
      id: z.string(),
      symbol: z.string(),
      side: z.string(),
      quantity: z.number(),
      entry_price: z.number(),
      current_price: z.number(),
      realized_pnl: z.number(),
      unrealized_pnl: z.number(),
      opened_at: z.string()
    })
  ),
  recent_fills: z.array(
    z.object({
      id: z.string(),
      symbol: z.string(),
      side: z.string(),
      quantity: z.number(),
      price: z.number(),
      event_time: z.string()
    })
  )
});

export const syncStatusSchema = z.array(syncCheckpointSchema);
export const symbolsSchema = z.array(symbolSchema);
export const candlesSchema = z.array(candleSchema);
export const healthStatusSchema = healthSchema;
