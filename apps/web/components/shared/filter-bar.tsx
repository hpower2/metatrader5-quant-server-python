import { cn } from "@/lib/utils/cn";

export function FilterBar({ className, children }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("flex flex-col gap-3 rounded-xl border border-border/60 bg-muted/30 p-3 lg:flex-row lg:items-center", className)}>
      {children}
    </div>
  );
}

