import { expect, test } from "@playwright/test";

test("backtest run flow", async ({ page }) => {
  await page.route("**/api/control/symbols", async (route) => {
    await route.fulfill({
      json: [
        {
          symbol: "EURUSD",
          description: "Euro vs US Dollar",
          path: "Forex",
          visible: true,
          digits: 5,
          trade_mode: 4
        }
      ]
    });
  });

  await page.route("**/api/control/backtests/run", async (route) => {
    await route.fulfill({
      json: {
        artifact_dir: "/tmp/backtest",
        config: {
          strategy_name: "eurusd_m1_5_20",
          signal_column: "signal",
          initial_cash: 100000,
          fee_bps: 1,
          slippage_bps: 1,
          fixed_quantity: 1
        },
        metrics: {
          final_equity: 101000,
          total_return: 0.01,
          max_drawdown: -0.02
        },
        trade_count: 12,
        equity_rows: 2,
        equity_curve: [
          { timestamp: "2026-04-10T00:00:00Z", equity: 100000 },
          { timestamp: "2026-04-10T01:00:00Z", equity: 101000 }
        ],
        trades: [
          {
            entry_time: "2026-04-10T00:00:00Z",
            exit_time: "2026-04-10T01:00:00Z",
            side: 1,
            quantity: 1,
            entry_price: 1.1,
            exit_price: 1.101,
            pnl: 1000
          }
        ]
      }
    });
  });

  await page.goto("/backtests");
  await page.getByRole("button", { name: /run backtest/i }).click();

  await expect(page.getByText("final_equity")).toBeVisible();
});
