"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuditPanel } from "@/components/shared/audit-panel";
import { DataTable } from "@/components/shared/data-table";
import { FormFeedback } from "@/components/shared/form-feedback";
import { FormFieldShell } from "@/components/shared/form-field-shell";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { StatusBadge } from "@/components/shared/status-badge";
import { SymbolSelector } from "@/components/shared/symbol-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDateTime, formatNumber } from "@/lib/formatters";
import { useSymbolOptions } from "@/hooks/use-symbol-options";
import { buildRiskWarnings, toPaperSignalRequest } from "@/features/paper-trading/lib/paper-trading";
import { usePaperStatus } from "@/features/paper-trading/hooks/use-paper-status";
import { paperSignalSchema } from "@/features/paper-trading/schemas/paper-signal-form";

export function PaperTradingPage() {
  const symbolsQuery = useSymbolOptions();
  const accountName = "default";
  const { query, signalMutation } = usePaperStatus(accountName);
  const form = useForm<z.input<typeof paperSignalSchema>, unknown, z.output<typeof paperSignalSchema>>({
    resolver: zodResolver(paperSignalSchema),
    defaultValues: {
      account_name: accountName,
      symbol: "EURUSD",
      side: "1",
      quantity: 1
    }
  });

  const onSubmit = form.handleSubmit((values) => signalMutation.mutate(toPaperSignalRequest(values)));
  const riskWarnings = buildRiskWarnings(query.data);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Execution monitor"
        title="Paper trading monitor"
        description="Track open paper positions, realized and unrealized PnL, recent fills, and submit manual directional signals for dry-run execution."
      />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionShell title="Signal console" description="Manual paper-only execution input with conservative form validation.">
          <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
            <FormFeedback
              className="md:col-span-2"
              message={signalMutation.error instanceof Error ? signalMutation.error.message : null}
            />
            <FormFieldShell label="Account" htmlFor="account_name" error={form.formState.errors.account_name?.message}>
              <Input id="account_name" {...form.register("account_name")} />
            </FormFieldShell>
            <FormFieldShell label="Symbol" description="Instrument to receive the manual paper signal.">
              <SymbolSelector value={form.watch("symbol")} onValueChange={(value) => form.setValue("symbol", value)} options={symbolsQuery.options} />
            </FormFieldShell>
            <FormFieldShell
              label="Side"
              htmlFor="side"
              error={form.formState.errors.side?.message}
              description="Use 1 for long, 0 for flatten, and -1 for short."
            >
              <Input id="side" {...form.register("side")} placeholder="1 long, 0 flat, -1 short" />
            </FormFieldShell>
            <FormFieldShell label="Quantity" htmlFor="quantity" error={form.formState.errors.quantity?.message}>
              <Input id="quantity" type="number" step="0.1" {...form.register("quantity")} />
            </FormFieldShell>
            <FormFieldShell label="Stop loss" htmlFor="stop_loss" error={form.formState.errors.stop_loss?.message}>
              <Input id="stop_loss" type="number" step="0.0001" {...form.register("stop_loss")} />
            </FormFieldShell>
            <FormFieldShell label="Take profit" htmlFor="take_profit" error={form.formState.errors.take_profit?.message}>
              <Input id="take_profit" type="number" step="0.0001" {...form.register("take_profit")} />
            </FormFieldShell>
            <div className="md:col-span-2">
              <FormFeedback
                tone="success"
                message={signalMutation.isSuccess ? "Signal submitted and paper state refreshed." : null}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={signalMutation.isPending}>
                {signalMutation.isPending ? "Submitting..." : "Submit signal"}
              </Button>
            </div>
          </form>
        </SectionShell>

        <SectionShell title="Account state" description="Live polled paper account summary with open risk.">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="text-sm text-muted-foreground">Account status</div>
              <div className="mt-3 flex items-center gap-2">
                <StatusBadge value={query.data?.account.status ?? "loading"} />
                <span className="text-sm text-muted-foreground">{query.data?.account.currency ?? "USD"}</span>
              </div>
              <div className="mt-4 text-2xl font-semibold">{formatNumber(query.data?.account.equity ?? 0, 2)}</div>
              <div className="text-sm text-muted-foreground">Equity</div>
            </div>
            <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="text-sm text-muted-foreground">Last mark</div>
              <div className="mt-4 text-sm">{query.data?.account.last_mark_to_market_at ? formatDateTime(query.data.account.last_mark_to_market_at) : "n/a"}</div>
            </div>
          </div>
          {riskWarnings.length ? <AuditPanel items={riskWarnings} /> : null}
        </SectionShell>
      </div>

      <SectionShell title="Active positions" description="Current open paper positions with live PnL polling.">
        <DataTable
          data={query.data?.open_positions ?? []}
          emptyMessage="No open positions."
          columns={[
            { key: "symbol", header: "Symbol", cell: (row) => row.symbol },
            { key: "side", header: "Side", cell: (row) => <StatusBadge value={row.side === "1" ? "long" : "short"} /> },
            { key: "qty", header: "Qty", cell: (row) => formatNumber(row.quantity, 2) },
            { key: "entry", header: "Entry", cell: (row) => formatNumber(row.entry_price, 5) },
            { key: "mark", header: "Mark", cell: (row) => formatNumber(row.current_price, 5) },
            { key: "upl", header: "Unrealized", cell: (row) => formatNumber(row.unrealized_pnl, 2) }
          ]}
        />
      </SectionShell>

      <SectionShell title="Execution journal" description="Recent fills and state transitions.">
        <DataTable
          data={query.data?.recent_fills ?? []}
          emptyMessage="No fills yet."
          columns={[
            { key: "symbol", header: "Symbol", cell: (row) => row.symbol },
            { key: "side", header: "Side", cell: (row) => row.side },
            { key: "qty", header: "Qty", cell: (row) => formatNumber(row.quantity, 2) },
            { key: "price", header: "Price", cell: (row) => formatNumber(row.price, 5) },
            { key: "event", header: "Event", cell: (row) => formatDateTime(row.event_time) }
          ]}
        />
      </SectionShell>
    </div>
  );
}
