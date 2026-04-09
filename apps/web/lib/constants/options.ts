export const timeframeOptions = ["M1", "M5", "M15"] as const;

export const featureOptionGroups = [
  { label: "Returns", options: ["simple_return", "log_return", "momentum_w5", "momentum_w20"] },
  { label: "Volatility", options: ["rolling_std_return_w5", "atr_w14", "volatility_w20"] },
  { label: "Structure", options: ["candle_range", "candle_body_size", "upper_wick_ratio", "lower_wick_ratio"] }
] as const;

