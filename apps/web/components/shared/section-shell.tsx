import { cn } from "@/lib/utils/cn";

export function SectionShell({
  title,
  description,
  actions,
  children,
  className
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("space-y-4 rounded-2xl border border-border/70 bg-card/70 p-5 backdrop-blur-sm", className)}>
      <div className="flex flex-col gap-3 border-b border-border/60 pb-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
          {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

