import { z } from "zod";

export const featureRunFormSchema = z.object({
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  higher_timeframe: z.string().optional(),
  feature_windows: z
    .string()
    .min(1)
    .refine((value) => value.split(",").every((part) => /^\s*\d+\s*$/.test(part)), "Use comma-separated integers.")
});

export const featureRunRequestSchema = z.object({
  symbol: z.string().min(1),
  timeframe: z.string().min(1),
  higher_timeframe: z.string().optional(),
  feature_config: z.object({
    windows: z.array(z.number().int().positive()).min(1),
    add_multi_timeframe: z.boolean()
  })
});

export type FeatureRunRequest = z.infer<typeof featureRunRequestSchema>;
