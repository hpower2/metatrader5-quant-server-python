"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { getSymbols } from "@/lib/api/queries";
import { queryKeys } from "@/lib/query/query-keys";

export function useSymbolOptions() {
  const query = useQuery({
    queryKey: queryKeys.symbols,
    queryFn: getSymbols
  });

  const options = useMemo(
    () =>
      (query.data ?? []).map((symbol) => ({
        label: symbol.symbol,
        value: symbol.symbol,
        description: symbol.description ?? "No description"
      })),
    [query.data]
  );

  return { ...query, options };
}

