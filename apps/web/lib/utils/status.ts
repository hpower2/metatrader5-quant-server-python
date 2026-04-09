import type { StatusTone } from "@/types/api";

export function statusToneFromValue(value: string | null | undefined): StatusTone {
  if (!value) {
    return "neutral";
  }

  const normalized = value.toLowerCase();
  if (["success", "healthy", "ok", "active"].includes(normalized)) {
    return "success";
  }
  if (["warning", "degraded", "pending", "starting"].includes(normalized)) {
    return "warning";
  }
  if (["failed", "error", "down", "unhealthy", "restarting"].includes(normalized)) {
    return "error";
  }
  return "info";
}

