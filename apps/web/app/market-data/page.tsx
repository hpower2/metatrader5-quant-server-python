import { Suspense } from "react";

import { MarketDataPage } from "@/features/market-data";

export default function MarketDataRoute() {
  return (
    <Suspense fallback={<div className="rounded-2xl border border-border/60 bg-card/70 p-6 text-sm text-muted-foreground">Loading market data explorer...</div>}>
      <MarketDataPage />
    </Suspense>
  );
}
