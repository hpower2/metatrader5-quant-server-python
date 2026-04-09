import { apiGet, apiPost } from "@/lib/api/http";
import {
  backtestRunResponseSchema,
  candlesSchema,
  datasetBuildResponseSchema,
  featureRunResponseSchema,
  healthStatusSchema,
  paperStatusSchema,
  symbolsSchema,
  syncStatusSchema
} from "@/lib/api/schemas";
import { z } from "zod";
import type {
  BacktestRunResponse,
  CandleRecord,
  DatasetBuildResponse,
  FeatureRunResponse,
  HealthStatus,
  PaperAccountStatus,
  SymbolSummary,
  SyncCheckpoint
} from "@/types/api";
import type { BacktestRunRequest } from "@/features/backtests/schemas/backtest-form";
import type { DatasetBuildRequest } from "@/features/datasets/schemas/dataset-form";
import type { FeatureRunRequest } from "@/features/features-explorer/schemas/feature-run";
import type { PaperSignalRequest } from "@/features/paper-trading/schemas/paper-signal-form";

export async function getHealthStatus(): Promise<HealthStatus> {
  return apiGet("/health", healthStatusSchema);
}

export async function getSyncStatus(): Promise<SyncCheckpoint[]> {
  return apiGet("/sync/status", syncStatusSchema);
}

export async function getSymbols(): Promise<SymbolSummary[]> {
  return apiGet("/symbols", symbolsSchema);
}

export async function getLatestCandles(symbol: string, timeframe: string, limit = 250): Promise<CandleRecord[]> {
  return apiGet(
    `/candles/latest?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`,
    candlesSchema
  );
}

export async function runFeatures(payload: FeatureRunRequest): Promise<FeatureRunResponse> {
  return apiPost("/features/run", payload, featureRunResponseSchema);
}

export async function buildDataset(payload: DatasetBuildRequest): Promise<DatasetBuildResponse> {
  return apiPost("/datasets/build", payload, datasetBuildResponseSchema);
}

export async function runBacktest(payload: BacktestRunRequest): Promise<BacktestRunResponse> {
  return apiPost("/backtests/run", payload, backtestRunResponseSchema);
}

export async function getPaperStatus(accountName = "default"): Promise<PaperAccountStatus> {
  return apiGet(`/paper/status?account_name=${encodeURIComponent(accountName)}`, paperStatusSchema);
}

export async function submitPaperSignal(payload: PaperSignalRequest): Promise<PaperAccountStatus> {
  return apiPost("/paper/signal", payload, paperStatusSchema);
}

export async function triggerSync(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  return apiPost("/sync/run", payload, z.record(z.string(), z.unknown()));
}
