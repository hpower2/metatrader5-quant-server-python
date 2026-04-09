"use client";

import { MetricCard } from "@/components/shared/metric-card";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { StatusBadge } from "@/components/shared/status-badge";
import { DataTable } from "@/components/shared/data-table";
import { AuditPanel } from "@/components/shared/audit-panel";
import { EmptyState } from "@/components/shared/empty-state";
import { SkeletonTable } from "@/components/shared/skeleton-table";
import { formatDateTime, formatNumber } from "@/lib/formatters";
import { useDashboardData } from "@/features/dashboard/hooks/use-dashboard-data";

export function DashboardPage() {
  const { healthQuery, syncQuery, paperQuery } = useDashboardData();
  const checkpoints = syncQuery.data ?? [];
  const paperStatus = paperQuery.data;
  const health = healthQuery.data;

  const syncFailures = checkpoints.filter((item) => item.last_status !== "success");
  const qualityAlerts = checkpoints
    .filter((item) => item.last_error)
    .map((item) => ({
      title: `${item.job_type} ${item.symbol ?? "global"} ${item.timeframe ?? ""}`.trim(),
      description: item.last_error ?? "Unknown issue",
      severity: item.last_status
    }));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Operations overview"
        title="Quant platform dashboard"
        description="Track ingestion health, quality signals, research workflow readiness, and paper trading state from a single control surface."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Sync checkpoints" value={checkpoints.length} secondaryLabel="Tracked jobs" />
        <MetricCard label="Failed jobs" value={syncFailures.length} secondaryLabel="Need attention" />
        <MetricCard
          label="Paper equity"
          value={paperStatus?.account.equity ?? 0}
          change={
            paperStatus
              ? (paperStatus.account.equity - paperStatus.account.cash) / Math.max(paperStatus.account.cash || 1, 1)
              : undefined
          }
          secondaryLabel={paperStatus?.account.currency ?? "USD"}
        />
        <MetricCard label="Open positions" value={paperStatus?.open_positions.length ?? 0} secondaryLabel="Live paper book" />
        <MetricCard label="System status" value={health?.status.toUpperCase() ?? "LOADING"} secondaryLabel="Control plane" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <SectionShell title="Checkpoint status" description="Latest ingestion and audit checkpoints by job scope.">
          {syncQuery.isLoading ? (
            <SkeletonTable />
          ) : (
            <DataTable
              data={checkpoints}
              columns={[
                { key: "job", header: "Job", cell: (row) => row.job_type },
                { key: "scope", header: "Scope", cell: (row) => `${row.symbol ?? "all"} / ${row.timeframe ?? "all"}` },
                { key: "status", header: "Status", cell: (row) => <StatusBadge value={row.last_status} /> },
                {
                  key: "last_sync",
                  header: "Last sync",
                  cell: (row) => (row.last_synced_at ? formatDateTime(row.last_synced_at) : "Never")
                },
                {
                  key: "cursor",
                  header: "Cursor",
                  cell: (row) => <span className="text-xs text-muted-foreground">{JSON.stringify(row.cursor)}</span>
                }
              ]}
            />
          )}
        </SectionShell>

        <SectionShell title="Health and quality" description="Data quality issues and platform status that should surface first.">
          <div className="space-y-4">
            <div className="rounded-xl border border-border/60 bg-muted/20 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Database</span>
                <StatusBadge value={health?.database.ok ? "healthy" : "failed"} />
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="text-sm text-muted-foreground">MT5 adapter</span>
                <StatusBadge value={health?.mt5?.status ?? "unknown"} />
              </div>
              <div className="mt-3 flex items-center justify-between">
                <span className="text-sm text-muted-foreground">MT5 connection</span>
                <StatusBadge value={health?.mt5?.mt5_connected ? "connected" : "disconnected"} />
              </div>
            </div>
            {qualityAlerts.length ? (
              <AuditPanel items={qualityAlerts} />
            ) : (
              <EmptyState title="No critical alerts" description="Recent sync and quality workflows have not surfaced errors." />
            )}
          </div>
        </SectionShell>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_1fr]">
        <SectionShell title="Paper trading summary" description="Current book and fill cadence from the paper execution provider.">
          {paperStatus ? (
            <DataTable
              data={paperStatus.open_positions}
              emptyMessage="No active paper positions"
              columns={[
                { key: "symbol", header: "Symbol", cell: (row) => row.symbol },
                { key: "side", header: "Side", cell: (row) => <StatusBadge value={row.side === "1" ? "long" : "short"} /> },
                { key: "qty", header: "Qty", cell: (row) => formatNumber(row.quantity, 2) },
                { key: "entry", header: "Entry", cell: (row) => formatNumber(row.entry_price, 5) },
                { key: "mark", header: "Mark", cell: (row) => formatNumber(row.current_price, 5) },
                { key: "pnl", header: "Unrealized PnL", cell: (row) => formatNumber(row.unrealized_pnl, 2) }
              ]}
            />
          ) : (
            <SkeletonTable />
          )}
        </SectionShell>

        <SectionShell title="Execution journal" description="Most recent fills recorded in paper mode.">
          {paperStatus ? (
            <DataTable
              data={paperStatus.recent_fills}
              emptyMessage="No fills recorded yet"
              columns={[
                { key: "symbol", header: "Symbol", cell: (row) => row.symbol },
                { key: "side", header: "Side", cell: (row) => row.side },
                { key: "qty", header: "Qty", cell: (row) => formatNumber(row.quantity, 2) },
                { key: "price", header: "Price", cell: (row) => formatNumber(row.price, 5) },
                { key: "event", header: "Event", cell: (row) => formatDateTime(row.event_time) }
              ]}
            />
          ) : (
            <SkeletonTable rows={4} />
          )}
        </SectionShell>
      </div>
    </div>
  );
}

