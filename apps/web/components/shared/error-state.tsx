import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

export function ErrorState({
  title,
  description,
  onRetry
}: {
  title: string;
  description: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center rounded-xl border border-danger/30 bg-danger/5 px-6 text-center">
      <AlertTriangle className="mb-3 h-8 w-8 text-danger" />
      <h3 className="text-base font-medium">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>
      {onRetry ? (
        <Button className="mt-4" onClick={onRetry} variant="outline">
          Retry
        </Button>
      ) : null}
    </div>
  );
}

