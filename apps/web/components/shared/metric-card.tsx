import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCompactNumber, formatPercent } from "@/lib/formatters";
import { cn } from "@/lib/utils/cn";

interface MetricCardProps {
  label: string;
  value: number | string;
  change?: number | undefined;
  secondaryLabel?: string | undefined;
}

export function MetricCard({ label, value, change, secondaryLabel }: MetricCardProps) {
  const isPositive = (change ?? 0) >= 0;

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div>
          <CardDescription>{label}</CardDescription>
          <CardTitle className="mt-2 text-3xl font-semibold">
            {typeof value === "number" ? formatCompactNumber(value) : value}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="flex items-center justify-between text-sm">
        <span className={cn("inline-flex items-center gap-1", change === undefined && "text-muted-foreground")}>
          {change !== undefined ? (
            <>
              {isPositive ? <ArrowUpRight className="h-4 w-4 text-success" /> : <ArrowDownRight className="h-4 w-4 text-danger" />}
              <span className={cn(isPositive ? "text-success" : "text-danger")}>{formatPercent(change)}</span>
            </>
          ) : (
            "No delta"
          )}
        </span>
        <span className="text-muted-foreground">{secondaryLabel}</span>
      </CardContent>
    </Card>
  );
}
