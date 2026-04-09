import { z } from "zod";

export const backtestFormSchema = z.object({
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  dataset_name: z
    .string()
    .optional()
    .transform((value) => {
      const normalized = value?.trim();
      return normalized ? normalized : undefined;
    }),
  dataset_split: z.enum(["train", "validation", "test"]).default("test"),
  fast_window: z.coerce.number().int().min(2).max(100),
  slow_window: z.coerce.number().int().min(3).max(300),
  initial_cash: z.coerce.number().min(1_000),
  fee_bps: z.coerce.number().min(0).max(50),
  slippage_bps: z.coerce.number().min(0).max(50),
  fixed_quantity: z.coerce.number().min(0.01)
}).refine((value) => value.fast_window < value.slow_window, {
  path: ["slow_window"],
  message: "Slow window must be greater than fast window."
});

export type BacktestFormValues = z.infer<typeof backtestFormSchema>;

export const backtestRunRequestSchema = z.object({
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  dataset_name: z.string().optional(),
  dataset_split: z.enum(["train", "validation", "test"]).default("test"),
  fast_window: z.number().int().min(2),
  slow_window: z.number().int().min(3),
  config: z.object({
    strategy_name: z.string().min(1),
    signal_column: z.literal("signal"),
    initial_cash: z.number().positive(),
    fee_bps: z.number().min(0),
    slippage_bps: z.number().min(0),
    fixed_quantity: z.number().positive()
  })
});

export type BacktestRunRequest = z.infer<typeof backtestRunRequestSchema>;
