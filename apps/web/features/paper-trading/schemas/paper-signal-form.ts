import { z } from "zod";

const optionalNumber = z.preprocess((value) => (value === "" || value === null ? undefined : value), z.coerce.number().optional());

export const paperSignalSchema = z.object({
  account_name: z.string().min(1),
  symbol: z.string().min(1),
  side: z.enum(["1", "0", "-1"]),
  quantity: z.coerce.number().min(0.01),
  stop_loss: optionalNumber,
  take_profit: optionalNumber
});

export type PaperSignalValues = z.infer<typeof paperSignalSchema>;

export const paperSignalRequestSchema = z.object({
  account_name: z.string().min(1),
  symbol: z.string().min(1),
  side: z.number().int().min(-1).max(1),
  quantity: z.number().positive(),
  stop_loss: z.number().optional(),
  take_profit: z.number().optional()
});

export type PaperSignalRequest = z.infer<typeof paperSignalRequestSchema>;
