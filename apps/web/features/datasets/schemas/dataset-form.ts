import { z } from "zod";

const optionalTimeframe = z.string().optional().transform((value) => {
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
});

export const datasetFormSchema = z.object({
  dataset_name: z.string().min(3),
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  total_bars: z.coerce.number().int().min(1000).max(500000),
  higher_timeframe: optionalTimeframe,
  feature_windows: z
    .string()
    .min(1)
    .refine((value) => value.split(",").every((part) => /^\s*\d+\s*$/.test(part)), "Use comma-separated integers."),
  horizon_bars: z.coerce.number().int().min(1).max(200),
  return_threshold: z.coerce.number().min(0),
  train_bars: z.coerce.number().int().min(1),
  validation_bars: z.coerce.number().int().min(0),
  test_bars: z.coerce.number().int().min(0),
  train_ratio: z.coerce.number().min(0.1).max(0.9),
  validation_ratio: z.coerce.number().min(0.05).max(0.4),
  test_ratio: z.coerce.number().min(0.05).max(0.4),
  walk_forward_train_bars: z.coerce.number().int().min(100),
  walk_forward_validation_bars: z.coerce.number().int().min(50),
  walk_forward_test_bars: z.coerce.number().int().min(50),
  walk_forward_step_bars: z.coerce.number().int().min(25)
}).refine((value) => Math.abs(value.train_ratio + value.validation_ratio + value.test_ratio - 1) < 0.0001, {
  message: "Train, validation, and test ratios must sum to 1.",
  path: ["test_ratio"]
});

export type DatasetFormValues = z.infer<typeof datasetFormSchema>;

export const datasetBuildRequestSchema = z.object({
  dataset_name: z.string().min(3),
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  total_bars: z.number().int().positive(),
  higher_timeframe: z.string().nullable(),
  split: z.object({
    train_ratio: z.number().min(0),
    validation_ratio: z.number().min(0),
    test_ratio: z.number().min(0),
    train_bars: z.number().int().positive(),
    validation_bars: z.number().int().min(0),
    test_bars: z.number().int().min(0).nullable().optional()
  }),
  walk_forward: z.object({
    train_bars: z.number().int().positive(),
    validation_bars: z.number().int().positive(),
    test_bars: z.number().int().positive(),
    step_bars: z.number().int().positive()
  }),
  feature_config: z.object({
    windows: z.array(z.number().int().positive()).min(1),
    add_multi_timeframe: z.boolean()
  }),
  label_config: z.object({
    horizon_bars: z.number().int().positive(),
    return_threshold: z.number().min(0)
  })
});

export type DatasetBuildRequest = z.infer<typeof datasetBuildRequestSchema>;
