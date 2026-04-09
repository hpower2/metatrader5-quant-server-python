import { cn } from "@/lib/utils/cn";

export function FormFieldShell({
  label,
  htmlFor,
  description,
  error,
  className,
  children
}: {
  label: string;
  htmlFor?: string | undefined;
  description?: string | undefined;
  error?: string | undefined;
  className?: string | undefined;
  children: React.ReactNode;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="space-y-1">
        <label htmlFor={htmlFor} className="text-sm font-medium text-foreground">
          {label}
        </label>
        {description ? <p className="text-xs text-muted-foreground">{description}</p> : null}
      </div>
      {children}
      {error ? <p className="text-xs text-danger">{error}</p> : null}
    </div>
  );
}
