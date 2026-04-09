"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ChartCard } from "@/components/charts/chart-card";
import { TimeSeriesChart } from "@/components/charts/timeseries-chart";
import { DataTable } from "@/components/shared/data-table";
import { FormFeedback } from "@/components/shared/form-feedback";
import { FormFieldShell } from "@/components/shared/form-field-shell";
import { MetricCard } from "@/components/shared/metric-card";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { SymbolSelector } from "@/components/shared/symbol-selector";
import { TimeframeSelector } from "@/components/shared/timeframe-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatNumber } from "@/lib/formatters";
import { useSymbolOptions } from "@/hooks/use-symbol-options";
import {
  toBacktestMetricsRows,
  toBacktestParameterRows,
  toBacktestRunRequest,
  toDrawdownSeries
} from "@/features/backtests/lib/backtest-run";
import { backtestFormSchema, type BacktestFormValues } from "@/features/backtests/schemas/backtest-form";
import { useBacktestRun } from "@/features/backtests/hooks/use-backtest-run";

export function BacktestsPage() {
  const symbolsQuery = useSymbolOptions();
  const mutation = useBacktestRun();
  const form = useForm<z.input<typeof backtestFormSchema>, unknown, z.output<typeof backtestFormSchema>>({
    resolver: zodResolver(backtestFormSchema),
    defaultValues: {
      symbol: "EURUSD",
      timeframe: "M1",
      dataset_name: "eurusd_m1_train70000_test10000",
      dataset_split: "test",
      fast_window: 5,
      slow_window: 20,
      initial_cash: 100000,
      fee_bps: 1,
      slippage_bps: 1,
      fixed_quantity: 1
    }
  });

  const onSubmit = form.handleSubmit((values) => mutation.mutate(toBacktestRunRequest(values)));
  const currentValues = form.getValues() as BacktestFormValues;
  const metricsRows = toBacktestMetricsRows(mutation.data).map((row) => ({
    metric: row.metric,
    value: formatNumber(row.value, 4)
  }));
  const parameterRows = toBacktestParameterRows(currentValues, mutation.data).map((row) => ({
    label: row.label,
    value: typeof row.value === "number" ? formatNumber(row.value, 4) : row.value
  }));
  const drawdownSeries = toDrawdownSeries(mutation.data);
  const datasetSplit = form.watch("dataset_split") ?? "test";
  const equitySeries = mutation.data?.equity_curve ?? [];
  const trades = mutation.data?.trades ?? [];
  const finalEquity = mutation.data?.metrics.final_equity ?? 0;
  const totalReturn = mutation.data?.metrics.total_return ?? 0;
  const maxDrawdown = mutation.data?.metrics.max_drawdown ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Strategy validation"
        title="Backtesting console"
        description="Run parameterized backtests against canonical warehouse data and inspect returned metrics with artifact-level traceability."
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SectionShell title="Strategy configuration" description="Moving-average crossover inputs with typed validation.">
          <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
            <FormFeedback
              className="md:col-span-2"
              message={mutation.error instanceof Error ? mutation.error.message : null}
            />
            <FormFieldShell label="Symbol" description="Instrument to backtest against canonical warehouse candles.">
              <SymbolSelector value={form.watch("symbol")} onValueChange={(value) => form.setValue("symbol", value)} options={symbolsQuery.options} />
            </FormFieldShell>
            <FormFieldShell label="Timeframe" description="Bar resolution for signal generation and execution.">
              <TimeframeSelector value={form.watch("timeframe")} onValueChange={(value) => form.setValue("timeframe", value)} />
            </FormFieldShell>
            <FormFieldShell
              label="Dataset name (optional)"
              htmlFor="dataset_name"
              error={form.formState.errors.dataset_name?.message}
              description="If set, backtest uses dataset split artifacts instead of direct warehouse candles."
            >
              <Input id="dataset_name" {...form.register("dataset_name")} />
            </FormFieldShell>
            <FormFieldShell
              label="Dataset split"
              description="Split to backtest when dataset name is provided."
              error={form.formState.errors.dataset_split?.message}
            >
              <Select value={datasetSplit} onValueChange={(value) => form.setValue("dataset_split", value as "train" | "validation" | "test")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select split" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="train">train</SelectItem>
                  <SelectItem value="validation">validation</SelectItem>
                  <SelectItem value="test">test</SelectItem>
                </SelectContent>
              </Select>
            </FormFieldShell>
            <FormFieldShell label="Fast window" htmlFor="fast_window" error={form.formState.errors.fast_window?.message}>
              <Input id="fast_window" type="number" {...form.register("fast_window")} />
            </FormFieldShell>
            <FormFieldShell label="Slow window" htmlFor="slow_window" error={form.formState.errors.slow_window?.message}>
              <Input id="slow_window" type="number" {...form.register("slow_window")} />
            </FormFieldShell>
            <FormFieldShell label="Initial cash" htmlFor="initial_cash" error={form.formState.errors.initial_cash?.message}>
              <Input id="initial_cash" type="number" {...form.register("initial_cash")} />
            </FormFieldShell>
            <FormFieldShell label="Fixed quantity" htmlFor="fixed_quantity" error={form.formState.errors.fixed_quantity?.message}>
              <Input id="fixed_quantity" type="number" step="0.1" {...form.register("fixed_quantity")} />
            </FormFieldShell>
            <FormFieldShell label="Fee bps" htmlFor="fee_bps" error={form.formState.errors.fee_bps?.message}>
              <Input id="fee_bps" type="number" step="0.1" {...form.register("fee_bps")} />
            </FormFieldShell>
            <FormFieldShell label="Slippage bps" htmlFor="slippage_bps" error={form.formState.errors.slippage_bps?.message}>
              <Input id="slippage_bps" type="number" step="0.1" {...form.register("slippage_bps")} />
            </FormFieldShell>
            <div className="md:col-span-2">
              <FormFeedback
                tone="success"
                message={mutation.data ? `Backtest completed with ${mutation.data.trade_count} trades.` : null}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Running backtest..." : "Run backtest"}
              </Button>
            </div>
          </form>
        </SectionShell>

        <div className="grid gap-6">
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard label="Final equity" value={finalEquity} secondaryLabel="Ending book value" />
            <MetricCard label="Total return" value={totalReturn * 100} secondaryLabel="Percent return" />
            <MetricCard label="Max drawdown" value={maxDrawdown * 100} secondaryLabel="Percent drawdown" />
          </div>
          <ChartCard title="Equity curve" description="Real equity points returned by the latest backtest run.">
            <TimeSeriesChart data={equitySeries} valueKey="equity" />
          </ChartCard>
          <ChartCard title="Drawdown" description="Derived drawdown series based on the returned equity curve.">
            <TimeSeriesChart data={drawdownSeries} valueKey="drawdown" stroke="#ef4444" />
          </ChartCard>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionShell title="Parameter summary" description="Exact runtime parameters and artifact location for the latest run.">
          <DataTable
            data={parameterRows}
            columns={[
              { key: "label", header: "Parameter", cell: (row) => row.label },
              { key: "value", header: "Value", cell: (row) => row.value }
            ]}
          />
        </SectionShell>
        <SectionShell title="Metrics" description="Performance metrics returned by the backtest service.">
          <DataTable
            data={metricsRows}
            emptyMessage="Run a backtest to populate metrics."
            columns={[
              { key: "metric", header: "Metric", cell: (row) => row.metric },
              { key: "value", header: "Value", cell: (row) => row.value }
            ]}
          />
        </SectionShell>
      </div>

      <SectionShell title="Trade log" description="Executed trades returned by the latest run.">
        <DataTable
          data={trades}
          emptyMessage="Run a backtest to populate the trade log."
          columns={[
            { key: "entry_time", header: "Entry", cell: (row) => row.entry_time },
            { key: "exit_time", header: "Exit", cell: (row) => row.exit_time },
            { key: "side", header: "Side", cell: (row) => (row.side > 0 ? "Long" : "Short") },
            { key: "quantity", header: "Qty", cell: (row) => formatNumber(row.quantity, 2) },
            { key: "entry_price", header: "Entry px", cell: (row) => formatNumber(row.entry_price, 5) },
            { key: "exit_price", header: "Exit px", cell: (row) => formatNumber(row.exit_price, 5) },
            { key: "pnl", header: "PnL", cell: (row) => formatNumber(row.pnl, 2) }
          ]}
        />
      </SectionShell>
    </div>
  );
}
