import type { CandleRecord } from "@/types/api";

export interface FeaturePreviewRow extends CandleRecord {
  simple_return: number | null;
  log_return: number | null;
  rolling_mean_close_w5: number | null;
  atr_w14: number | null;
  rsi_w14: number | null;
}

export function buildFeaturePreview(candles: CandleRecord[]): FeaturePreviewRow[] {
  return candles.map((candle, index) => {
    const previous = candles[index - 1];
    const last5 = candles.slice(Math.max(0, index - 4), index + 1);
    const last14 = candles.slice(Math.max(0, index - 13), index + 1);

    const simpleReturn = previous ? candle.close / previous.close - 1 : null;
    const logReturn = previous ? Math.log(candle.close / previous.close) : null;
    const rollingMean = last5.length === 5 ? last5.reduce((sum, item) => sum + item.close, 0) / 5 : null;

    const atr =
      last14.length === 14
        ? last14.reduce((sum, item, currentIndex) => {
            const prior = last14[currentIndex - 1];
            const prevClose = prior?.close ?? item.close;
            return sum + Math.max(item.high - item.low, Math.abs(item.high - prevClose), Math.abs(item.low - prevClose));
          }, 0) / 14
        : null;

    const gains = last14.slice(1).map((item, currentIndex) => {
      const baseline = last14[currentIndex];
      return baseline ? Math.max(item.close - baseline.close, 0) : 0;
    });
    const losses = last14.slice(1).map((item, currentIndex) => {
      const baseline = last14[currentIndex];
      return baseline ? Math.max(baseline.close - item.close, 0) : 0;
    });
    const avgGain = gains.length === 13 ? gains.reduce((sum, item) => sum + item, 0) / gains.length : null;
    const avgLoss = losses.length === 13 ? losses.reduce((sum, item) => sum + item, 0) / losses.length : null;
    const rs = avgGain !== null && avgLoss !== null && avgLoss !== 0 ? avgGain / avgLoss : null;
    const rsi = rs !== null ? 100 - 100 / (1 + rs) : null;

    return {
      ...candle,
      simple_return: simpleReturn,
      log_return: logReturn,
      rolling_mean_close_w5: rollingMean,
      atr_w14: atr,
      rsi_w14: rsi
    };
  });
}
