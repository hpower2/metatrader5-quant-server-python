"use client";

import { useMemo, useState } from "react";

import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { DataTable } from "@/components/shared/data-table";
import { FilterBar } from "@/components/shared/filter-bar";
import { FormFieldShell } from "@/components/shared/form-field-shell";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { SymbolSelector } from "@/components/shared/symbol-selector";
import { TimeframeSelector } from "@/components/shared/timeframe-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatNumber } from "@/lib/formatters";
import { toCandlestickData } from "@/lib/utils/chart-mappers";
import { useInstrumentFilters } from "@/hooks/use-instrument-filters";
import { useSymbolOptions } from "@/hooks/use-symbol-options";
import { buildFeatureRunRequest } from "@/features/features-explorer/lib/feature-run";
import { useFeaturePreview } from "@/features/features-explorer/hooks/use-feature-preview";

export function FeaturesExplorerPage() {
  const symbolsQuery = useSymbolOptions();
  const { symbol, timeframe, setSymbol, setTimeframe } = useInstrumentFilters({ symbol: "EURUSD", timeframe: "M1" });
  const [featureWindows, setFeatureWindows] = useState("5,14,20,50");
  const [higherTimeframe, setHigherTimeframe] = useState("M5");
  const { previewRows, runMutation } = useFeaturePreview(symbol, timeframe);

  const overlay = useMemo(
    () => [
      {
        name: "rolling_mean_close_w5",
        values: previewRows
          .filter((row) => row.rolling_mean_close_w5 !== null)
          .map((row) => ({ time: row.timestamp, value: row.rolling_mean_close_w5 as number }))
      }
    ],
    [previewRows]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Feature research"
        title="Feature explorer"
        description="Preview leakage-safe features on top of recent candles, then trigger the backend feature workflow to materialize a reusable artifact."
        actions={
          <Button
            onClick={() =>
              runMutation.mutate(
                buildFeatureRunRequest({
                  symbol,
                  timeframe,
                  higherTimeframe,
                  featureWindows
                })
              )
            }
          >
            Generate artifact
          </Button>
        }
      />

      <FilterBar>
        <SymbolSelector value={symbol} onValueChange={setSymbol} options={symbolsQuery.options} />
        <TimeframeSelector value={timeframe} onValueChange={setTimeframe} />
      </FilterBar>

      <SectionShell title="Generation controls" description="Feature artifact settings kept separate from the preview chart.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <FormFieldShell label="Feature windows" htmlFor="feature_windows" description="Comma-separated rolling windows for engineered features.">
            <Input id="feature_windows" value={featureWindows} onChange={(event) => setFeatureWindows(event.target.value)} />
          </FormFieldShell>
          <FormFieldShell label="Higher timeframe" description="Optional higher timeframe join for feature generation.">
            <TimeframeSelector value={higherTimeframe} onValueChange={setHigherTimeframe} />
          </FormFieldShell>
          <FormFieldShell label="Mutation state" description="Current backend generation lifecycle.">
            <div className="flex h-10 items-center rounded-lg border border-border/60 bg-muted/20 px-3 text-sm">{runMutation.status}</div>
          </FormFieldShell>
        </div>
      </SectionShell>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <SectionShell title="Price and overlay" description="Candlestick view with a rolling mean overlay for fast visual validation.">
          <CandlestickChart data={toCandlestickData(previewRows)} overlaySeries={overlay} />
        </SectionShell>
        <SectionShell title="Artifact status" description="Backend feature generation response and preview stats.">
          <dl className="grid gap-3 rounded-xl border border-border/60 bg-muted/20 p-4 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Preview rows</dt>
              <dd>{previewRows.length}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Computed columns</dt>
              <dd>5+</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Mutation state</dt>
              <dd>{runMutation.status}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Feature windows</dt>
              <dd>{featureWindows}</dd>
            </div>
            {runMutation.data ? (
              <>
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Artifact rows</dt>
                  <dd>{runMutation.data.rows}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-muted-foreground">Artifact path</dt>
                  <dd className="truncate text-right text-xs">{runMutation.data.artifact_path}</dd>
                </div>
              </>
            ) : null}
          </dl>
        </SectionShell>
      </div>

      <SectionShell title="Feature table" description="Local preview table for immediate inspection before a persisted run.">
        <DataTable
          data={previewRows.slice(-80).reverse()}
          columns={[
            { key: "timestamp", header: "Timestamp", cell: (row) => row.timestamp },
            { key: "close", header: "Close", cell: (row) => formatNumber(row.close, 5) },
            { key: "ret", header: "Simple return", cell: (row) => formatNumber(row.simple_return ?? 0, 6) },
            { key: "log", header: "Log return", cell: (row) => formatNumber(row.log_return ?? 0, 6) },
            { key: "mean", header: "Rolling mean", cell: (row) => formatNumber(row.rolling_mean_close_w5 ?? 0, 5) },
            { key: "atr", header: "ATR 14", cell: (row) => formatNumber(row.atr_w14 ?? 0, 5) },
            { key: "rsi", header: "RSI 14", cell: (row) => formatNumber(row.rsi_w14 ?? 0, 2) }
          ]}
        />
      </SectionShell>
    </div>
  );
}
