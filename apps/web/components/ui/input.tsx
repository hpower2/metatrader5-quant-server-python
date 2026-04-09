import { cn } from "@/lib/utils/cn";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-lg border border-border bg-input/70 px-3 py-2 text-sm text-foreground outline-none transition ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-primary",
        className
      )}
      {...props}
    />
  );
}

