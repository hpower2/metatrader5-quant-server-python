"use client";

import { useCallback, useMemo, useTransition } from "react";
import type { Route } from "next";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

interface InstrumentFilterDefaults {
  symbol: string;
  timeframe: string;
}

export function useInstrumentFilters(defaults: InstrumentFilterDefaults) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const paramsString = searchParams.toString();

  const filters = useMemo(
    () => ({
      symbol: searchParams.get("symbol") ?? defaults.symbol,
      timeframe: searchParams.get("timeframe") ?? defaults.timeframe
    }),
    [defaults.symbol, defaults.timeframe, searchParams]
  );

  const updateFilter = useCallback(
    (key: "symbol" | "timeframe", value: string) => {
      const nextParams = new URLSearchParams(paramsString);
      nextParams.set(key, value);

      startTransition(() => {
        router.replace(`${pathname}?${nextParams.toString()}` as Route, { scroll: false });
      });
    },
    [paramsString, pathname, router]
  );

  return {
    ...filters,
    isPending,
    setSymbol: (value: string) => updateFilter("symbol", value),
    setTimeframe: (value: string) => updateFilter("timeframe", value)
  };
}
