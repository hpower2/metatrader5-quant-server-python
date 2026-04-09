"use client";

import { useQueries } from "@tanstack/react-query";

import { getHealthStatus, getPaperStatus, getSyncStatus } from "@/lib/api/queries";
import { queryKeys } from "@/lib/query/query-keys";

export function useDashboardData() {
  const [healthQuery, syncQuery, paperQuery] = useQueries({
    queries: [
      { queryKey: queryKeys.health, queryFn: getHealthStatus },
      { queryKey: queryKeys.syncStatus, queryFn: getSyncStatus },
      { queryKey: queryKeys.paperStatus("default"), queryFn: () => getPaperStatus("default"), refetchInterval: 10_000 }
    ]
  });

  return {
    healthQuery,
    syncQuery,
    paperQuery
  };
}
