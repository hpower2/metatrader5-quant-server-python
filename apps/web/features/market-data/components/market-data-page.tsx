"use client";

import { useMemo } from "react";

import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { VolumeChart } from "@/components/charts/volume-chart";
import { DataTable } from "@/components/shared/data-table";
import { ErrorState } from "@/components/shared/error-state";
import { FilterBar } from "@/components/shared/filter-bar";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { StatusBadge } from "@/components/shared/status-badge";
import { SymbolSelector } from "@/components/shared/symbol-selector";
import { TimeframeSelector } from "@/components/shared/timeframe-selector";
import { SkeletonTable } from "@/components/shared/skeleton-table";
import { formatDateTime, formatNumber } from "@/lib/formatters";
import { toCandlestickData, toVolumeSeries } from "@/lib/utils/chart-mappers";
import { useInstrumentFilters } from "@/hooks/use-instrument-filters";
import { useSymbolOptions } from "@/hooks/use-symbol-options";
import { useMarketData } from "@/features/market-data/hooks/use-market-data";

export function MarketDataPage() {
  const symbolsQuery = useSymbolOptions();
  const { symbol, timeframe, setSymbol, setTimeframe } = useInstrumentFilters({ symbol: "EURUSD", timeframe: "M1" });
  const candlesQuery = useMarketData(symbol, timeframe, 240);

  const selectedSymbol = useMemo(
    () => symbolsQuery.data?.find((item) => item.symbol === symbol) ?? null,
    [symbol, symbolsQuery.data]
  );
  const anomalyRows = (candlesQuery.data ?? []).filter((row) => row.quality_flags.length > 0);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Market data"
        title="Market data explorer"
        description="Inspect canonical candles, surface anomalies, and cross-check the latest synced instrument metadata before you trust a research run."
      />

      <FilterBar>
        <SymbolSelector value={symbol} onValueChange={setSymbol} options={symbolsQuery.options} />
        <TimeframeSelector value={timeframe} onValueChange={setTimeframe} />
      </FilterBar>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_0.9fr]">
        <SectionShell title="Candlestick view" description="Canonical candles with current timeframe selection.">
          <CandlestickChart data={toCandlestickData(candlesQuery.data ?? [])} />
          <div className="mt-4">
            <VolumeChart data={toVolumeSeries(candlesQuery.data ?? [])} />
          </div>
        </SectionShell>

        <SectionShell title="Symbol metadata" description="Cached instrument metadata and anomaly rollup for the selected view.">
          <div className="space-y-4">
            <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
              <dl className="grid gap-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Symbol</dt>
                  <dd>{selectedSymbol?.symbol ?? symbol}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Description</dt>
                  <dd>{selectedSymbol?.description ?? "Unknown"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Digits</dt>
                  <dd>{selectedSymbol?.digits ?? "n/a"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Visible</dt>
                  <dd>
                    <StatusBadge value={selectedSymbol?.visible ? "visible" : "hidden"} />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Trade mode</dt>
                  <dd>{selectedSymbol?.trade_mode ?? "n/a"}</dd>
                </div>
              </dl>
            </div>
            <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Bars with quality flags</span>
                <StatusBadge value={anomalyRows.length ? "warning" : "healthy"} />
              </div>
              <p className="mt-3 text-3xl font-semibold">{anomalyRows.length}</p>
            </div>
          </div>
        </SectionShell>
      </div>

      <SectionShell title="Raw candle table" description="Latest canonical candles with preserved quality flags.">
        {candlesQuery.isLoading ? (
          <SkeletonTable rows={8} columns={7} />
        ) : candlesQuery.isError ? (
          <ErrorState
            title="Unable to load candles"
            description={candlesQuery.error instanceof Error ? candlesQuery.error.message : "The market data query failed."}
            onRetry={() => candlesQuery.refetch()}
          />
        ) : (
          <DataTable
            data={candlesQuery.data ?? []}
            columns={[
              { key: "timestamp", header: "Timestamp", cell: (row) => formatDateTime(row.timestamp) },
              { key: "open", header: "Open", cell: (row) => formatNumber(row.open, 5) },
              { key: "high", header: "High", cell: (row) => formatNumber(row.high, 5) },
              { key: "low", header: "Low", cell: (row) => formatNumber(row.low, 5) },
              { key: "close", header: "Close", cell: (row) => formatNumber(row.close, 5) },
              { key: "volume", header: "Tick volume", cell: (row) => formatNumber(row.tick_volume, 0) },
              {
                key: "flags",
                header: "Flags",
                cell: (row) =>
                  row.quality_flags.length ? (
                    <div className="flex flex-wrap gap-1">
                      {row.quality_flags.map((flag) => (
                        <StatusBadge key={flag} value={flag} />
                      ))}
                    </div>
                  ) : (
                    <StatusBadge value="clean" />
                  )
              }
            ]}
          />
        )}
      </SectionShell>
    </div>
  );
}
