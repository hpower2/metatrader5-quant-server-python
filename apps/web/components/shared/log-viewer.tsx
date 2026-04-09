import { formatDateTime } from "@/lib/formatters";

export function LogViewer({ entries }: { entries: Array<{ label: string; value: string; timestamp?: string }> }) {
  return (
    <div className="max-h-80 overflow-auto rounded-xl border border-border/60 bg-black/20 p-3 font-mono text-xs">
      <div className="space-y-2">
        {entries.map((entry, index) => (
          <div key={`${entry.label}-${index}`} className="grid grid-cols-[10rem_1fr] gap-3 rounded-md bg-black/20 px-3 py-2">
            <div className="text-muted-foreground">
              <div>{entry.label}</div>
              {entry.timestamp ? <div>{formatDateTime(entry.timestamp)}</div> : null}
            </div>
            <div className="break-all text-foreground">{entry.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

