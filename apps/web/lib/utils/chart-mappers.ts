import type { CandleRecord } from "@/types/api";

export function toCandlestickData(candles: CandleRecord[]) {
  return candles.map((candle) => ({
    time: candle.timestamp,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: candle.tick_volume
  }));
}

export function toVolumeSeries(candles: CandleRecord[]) {
  return candles.map((candle) => ({
    timestamp: candle.timestamp,
    volume: candle.tick_volume
  }));
}
