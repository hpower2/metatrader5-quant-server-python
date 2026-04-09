import type { FeatureRunRequest } from "@/features/features-explorer/schemas/feature-run";

export function parseFeatureWindows(value: string) {
  return value
    .split(",")
    .map((part) => Number(part.trim()))
    .filter((part) => Number.isFinite(part) && part > 0);
}

export function buildFeatureRunRequest({
  symbol,
  timeframe,
  higherTimeframe,
  featureWindows
}: {
  symbol: string;
  timeframe: string;
  higherTimeframe?: string;
  featureWindows: string;
}): FeatureRunRequest {
  const windows = parseFeatureWindows(featureWindows);

  return {
    symbol,
    timeframe,
    higher_timeframe: higherTimeframe,
    feature_config: {
      windows,
      add_multi_timeframe: Boolean(higherTimeframe)
    }
  };
}
