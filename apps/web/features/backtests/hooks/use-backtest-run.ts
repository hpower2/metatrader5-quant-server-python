"use client";

import { useMutation } from "@tanstack/react-query";

import { runBacktest } from "@/lib/api/queries";
import type { BacktestRunRequest } from "@/features/backtests/schemas/backtest-form";

export function useBacktestRun() {
  return useMutation({
    mutationFn: (payload: BacktestRunRequest) => runBacktest(payload)
  });
}
