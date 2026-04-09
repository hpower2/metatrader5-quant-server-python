import { Badge } from "@/components/ui/badge";
import { statusToneFromValue } from "@/lib/utils/status";

export function StatusBadge({ value }: { value: string | null | undefined }) {
  const tone = statusToneFromValue(value);
  const variant = tone === "neutral" ? "default" : tone;

  return <Badge variant={variant}>{value ?? "unknown"}</Badge>;
}

