"use client";

import { useQuery } from "@tanstack/react-query";

import { getLatestCandles } from "@/lib/api/queries";
import { queryKeys } from "@/lib/query/query-keys";

export function useMarketData(symbol: string, timeframe: string, limit = 300) {
  return useQuery({
    queryKey: queryKeys.candles(symbol, timeframe, limit),
    queryFn: () => getLatestCandles(symbol, timeframe, limit),
    enabled: Boolean(symbol && timeframe)
  });
}

