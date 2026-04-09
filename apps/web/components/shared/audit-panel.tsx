import { TriangleAlert } from "lucide-react";

import { StatusBadge } from "@/components/shared/status-badge";

export function AuditPanel({
  items
}: {
  items: Array<{ title: string; description: string; severity: string }>;
}) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={`${item.title}-${item.description}`} className="flex items-start gap-3 rounded-xl border border-border/60 bg-muted/20 p-3">
          <TriangleAlert className="mt-0.5 h-4 w-4 text-warning" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="font-medium">{item.title}</h4>
              <StatusBadge value={item.severity} />
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

