import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";

import { BacktestsPage } from "@/features/backtests/components/backtests-page";

const mutate = vi.fn();

vi.mock("@/hooks/use-symbol-options", () => ({
  useSymbolOptions: () => ({
    options: [{ label: "EURUSD", value: "EURUSD" }],
    data: [{ symbol: "EURUSD", description: "Euro vs US Dollar", path: "Forex", visible: true, digits: 5, trade_mode: 4 }]
  })
}));

vi.mock("@/features/backtests/hooks/use-backtest-run", () => ({
  useBacktestRun: () => ({
    mutate,
    isPending: false,
    data: null
  })
}));

function renderWithProviders() {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <BacktestsPage />
    </QueryClientProvider>
  );
}

describe("BacktestsPage", () => {
  it("submits the run mutation with typed payload", async () => {
    const user = userEvent.setup();
    renderWithProviders();

    await user.click(screen.getByRole("button", { name: /run backtest/i }));

    expect(mutate).toHaveBeenCalledTimes(1);
    expect(mutate).toHaveBeenCalledWith({
      symbol: "EURUSD",
      timeframe: "M1",
      dataset_name: "eurusd_m1_train70000_test10000",
      dataset_split: "test",
      fast_window: 5,
      slow_window: 20,
      config: {
        strategy_name: "eurusd_m1_5_20",
        signal_column: "signal",
        initial_cash: 100000,
        fee_bps: 1,
        slippage_bps: 1,
        fixed_quantity: 1
      }
    });
  });
});
