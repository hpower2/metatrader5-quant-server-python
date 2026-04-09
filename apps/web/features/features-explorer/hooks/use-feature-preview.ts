"use client";

import { useMemo } from "react";
import { useMutation } from "@tanstack/react-query";

import { runFeatures } from "@/lib/api/queries";
import { buildFeaturePreview } from "@/features/features-explorer/lib/feature-preview";
import { useMarketData } from "@/features/market-data/hooks/use-market-data";
import type { FeatureRunRequest } from "@/features/features-explorer/schemas/feature-run";

export function useFeaturePreview(symbol: string, timeframe: string) {
  const candlesQuery = useMarketData(symbol, timeframe, 240);
  const previewRows = useMemo(() => buildFeaturePreview(candlesQuery.data ?? []), [candlesQuery.data]);
  const runMutation = useMutation({
    mutationFn: (payload: FeatureRunRequest) => runFeatures(payload)
  });

  return {
    candlesQuery,
    previewRows,
    runMutation
  };
}
