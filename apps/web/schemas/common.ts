import { z } from "zod";

export const syncCheckpointSchema = z.object({
  job_type: z.string(),
  symbol: z.string().nullable(),
  timeframe: z.string().nullable(),
  last_synced_at: z.string().nullable(),
  last_ingested_bar_at: z.string().nullable(),
  last_status: z.string(),
  last_error: z.string().nullable(),
  cursor: z.record(z.string(), z.unknown())
});

export const symbolSchema = z.object({
  symbol: z.string(),
  description: z.string().nullable(),
  path: z.string().nullable(),
  visible: z.boolean(),
  digits: z.number().nullable(),
  trade_mode: z.number().nullable()
});

export const candleSchema = z.object({
  symbol: z.string(),
  timeframe: z.string(),
  timestamp: z.string(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  tick_volume: z.number(),
  real_volume: z.number(),
  spread: z.number(),
  quality_flags: z.array(z.string())
});

export const healthSchema = z.object({
  status: z.string(),
  database: z.object({
    ok: z.boolean(),
    error: z.string().nullable()
  }),
  mt5: z
    .object({
      status: z.string().optional(),
      mt5_initialized: z.boolean().optional(),
      mt5_connected: z.boolean().optional(),
      error: z.string().optional()
    })
    .nullable()
});

