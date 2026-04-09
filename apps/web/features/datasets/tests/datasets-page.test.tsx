import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";

import { DatasetsPage } from "@/features/datasets/components/datasets-page";

const mutate = vi.fn();

vi.mock("@/hooks/use-symbol-options", () => ({
  useSymbolOptions: () => ({
    options: [{ label: "EURUSD", value: "EURUSD" }],
    data: [{ symbol: "EURUSD", description: "Euro vs US Dollar", path: "Forex", visible: true, digits: 5, trade_mode: 4 }]
  })
}));

vi.mock("@/features/datasets/hooks/use-dataset-build", () => ({
  useDatasetBuild: () => ({
    mutate,
    isPending: false,
    data: null
  })
}));

function renderWithProviders() {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <DatasetsPage />
    </QueryClientProvider>
  );
}

describe("DatasetsPage", () => {
  it("submits the build mutation", async () => {
    const user = userEvent.setup();
    renderWithProviders();

    await user.click(screen.getByRole("button", { name: /build dataset/i }));

    expect(mutate).toHaveBeenCalledTimes(1);
    expect(mutate).toHaveBeenCalledWith({
      dataset_name: "eurusd_m1_train70000_test10000",
      symbol: "EURUSD",
      timeframe: "M1",
      total_bars: 80000,
      higher_timeframe: "M5",
      split: {
        train_ratio: 0.7,
        validation_ratio: 0.15,
        test_ratio: 0.15,
        train_bars: 70000,
        validation_bars: 0,
        test_bars: null
      },
      walk_forward: {
        train_bars: 2000,
        validation_bars: 500,
        test_bars: 500,
        step_bars: 500
      },
      feature_config: {
        windows: [5, 14, 20, 50],
        add_multi_timeframe: true
      },
      label_config: {
        horizon_bars: 5,
        return_threshold: 0.0005
      }
    });
  });
});
