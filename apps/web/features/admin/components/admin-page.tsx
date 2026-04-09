"use client";

import { DataTable } from "@/components/shared/data-table";
import { LogViewer } from "@/components/shared/log-viewer";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDateTime } from "@/lib/formatters";
import { useAdminData } from "@/features/admin/hooks/use-admin-data";

export function AdminPage() {
  const { healthQuery, syncQuery, symbolsQuery } = useAdminData();

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform operations"
        title="Admin and operations"
        description="Review service health, sync coverage, symbol visibility, and recent operational signals from the internal quant platform."
      />

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <SectionShell title="Service health" description="Current health payload from the quant control API.">
          <DataTable
            data={[
              { label: "Control plane", value: healthQuery.data?.status ?? "loading" },
              { label: "Database", value: healthQuery.data?.database.ok ? "healthy" : "failed" },
              { label: "MT5 connected", value: healthQuery.data?.mt5?.mt5_connected ? "connected" : "disconnected" },
              { label: "MT5 initialized", value: healthQuery.data?.mt5?.mt5_initialized ? "initialized" : "not_ready" }
            ]}
            columns={[
              { key: "label", header: "Component", cell: (row) => row.label },
              { key: "value", header: "Status", cell: (row) => <StatusBadge value={row.value} /> }
            ]}
          />
        </SectionShell>

        <SectionShell title="Config visibility" description="Operationally useful surface-level config and counts.">
          <LogViewer
            entries={[
              { label: "Known symbols", value: String(symbolsQuery.data?.length ?? 0) },
              { label: "Tracked checkpoints", value: String(syncQuery.data?.length ?? 0) },
              { label: "Database error", value: healthQuery.data?.database.error ?? "none" }
            ]}
          />
        </SectionShell>
      </div>

      <SectionShell title="Sync and audit status" description="Operational view into checkpoint coverage and failures.">
        <DataTable
          data={syncQuery.data ?? []}
          columns={[
            { key: "job", header: "Job", cell: (row) => row.job_type },
            { key: "scope", header: "Scope", cell: (row) => `${row.symbol ?? "all"} / ${row.timeframe ?? "all"}` },
            { key: "status", header: "Status", cell: (row) => <StatusBadge value={row.last_status} /> },
            { key: "sync", header: "Last sync", cell: (row) => (row.last_synced_at ? formatDateTime(row.last_synced_at) : "Never") },
            { key: "error", header: "Last error", cell: (row) => row.last_error ?? "None" }
          ]}
        />
      </SectionShell>
    </div>
  );
}
