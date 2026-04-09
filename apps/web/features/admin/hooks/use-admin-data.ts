"use client";

import { useQueries } from "@tanstack/react-query";

import { getHealthStatus, getSyncStatus, getSymbols } from "@/lib/api/queries";
import { queryKeys } from "@/lib/query/query-keys";

export function useAdminData() {
  const [healthQuery, syncQuery, symbolsQuery] = useQueries({
    queries: [
      { queryKey: queryKeys.health, queryFn: getHealthStatus, refetchInterval: 15_000 },
      { queryKey: queryKeys.syncStatus, queryFn: getSyncStatus, refetchInterval: 15_000 },
      { queryKey: queryKeys.symbols, queryFn: getSymbols }
    ]
  });

  return {
    healthQuery,
    syncQuery,
    symbolsQuery
  };
}
