import { Suspense } from "react";

import { FeaturesExplorerPage } from "@/features/features-explorer";

export default function FeaturesExplorerRoute() {
  return (
    <Suspense fallback={<div className="rounded-2xl border border-border/60 bg-card/70 p-6 text-sm text-muted-foreground">Loading feature explorer...</div>}>
      <FeaturesExplorerPage />
    </Suspense>
  );
}
