import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

import { cn } from "@/lib/utils/cn";

type FeedbackTone = "error" | "success" | "info";

const toneStyles: Record<FeedbackTone, string> = {
  error: "border-danger/30 bg-danger/5 text-danger",
  success: "border-success/30 bg-success/10 text-success",
  info: "border-primary/25 bg-primary/8 text-primary"
};

const toneIcons = {
  error: AlertTriangle,
  success: CheckCircle2,
  info: Info
} satisfies Record<FeedbackTone, React.ComponentType<{ className?: string }>>;

export function FormFeedback({
  message,
  tone = "error",
  className
}: {
  message?: string | null | undefined;
  tone?: FeedbackTone | undefined;
  className?: string | undefined;
}) {
  if (!message) {
    return null;
  }

  const Icon = toneIcons[tone];

  return (
    <div className={cn("flex items-start gap-2 rounded-xl border px-3 py-2 text-sm", toneStyles[tone], className)} role="status">
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <p>{message}</p>
    </div>
  );
}
