"use client";

import { useEffect, useRef } from "react";
import type { ISeriesApi, UTCTimestamp } from "lightweight-charts";
import { CandlestickSeries, ColorType, LineSeries, createChart } from "lightweight-charts";

import { EmptyState } from "@/components/shared/empty-state";
import { cn } from "@/lib/utils/cn";

export interface CandlestickDatum {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface CandlestickChartProps {
  data: CandlestickDatum[];
  overlaySeries?: Array<{ name: string; values: Array<{ time: string; value: number }> }>;
  className?: string;
}

export function CandlestickChart({ data, overlaySeries = [], className }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ReturnType<typeof createChart> | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) {
      return;
    }

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#dbe6ef"
      },
      grid: {
        vertLines: { color: "rgba(120, 136, 153, 0.12)" },
        horzLines: { color: "rgba(120, 136, 153, 0.12)" }
      },
      rightPriceScale: {
        borderColor: "rgba(120, 136, 153, 0.2)"
      },
      timeScale: {
        borderColor: "rgba(120, 136, 153, 0.2)"
      }
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
      borderVisible: false
    });

    candleSeries.setData(
      data.map((item) => ({
        time: Math.floor(new Date(item.time).getTime() / 1000) as UTCTimestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close
      }))
    );

    overlaySeries.forEach((overlay, index) => {
      const line = chart.addSeries(LineSeries, {
        color: index % 2 === 0 ? "#1ecbe1" : "#ff9b35",
        lineWidth: 2,
        priceLineVisible: false
      });
      line.setData(
        overlay.values.map((item) => ({
          time: Math.floor(new Date(item.time).getTime() / 1000) as UTCTimestamp,
          value: item.value
        }))
      );
    });

    chart.timeScale().fitContent();

    chartRef.current = chart;
    seriesRef.current = candleSeries;

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [data, overlaySeries]);

  if (data.length === 0) {
    return <EmptyState title="No market candles" description="Choose a symbol and timeframe to load candlestick data." />;
  }

  return <div ref={containerRef} className={cn("h-[26rem] w-full", className)} />;
}
