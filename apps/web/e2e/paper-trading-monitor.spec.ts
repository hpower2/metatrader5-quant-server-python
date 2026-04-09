import { expect, test } from "@playwright/test";

test("paper trading monitor flow", async ({ page }) => {
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

  await page.route("**/api/control/paper/status?account_name=default", async (route) => {
    await route.fulfill({
      json: {
        account: {
          name: "default",
          currency: "USD",
          cash: 100000,
          equity: 100120,
          status: "active",
          last_mark_to_market_at: "2026-04-10T00:00:00Z"
        },
        open_positions: [
          {
            id: "1",
            symbol: "EURUSD",
            side: "1",
            quantity: 1,
            entry_price: 1.1,
            current_price: 1.1012,
            realized_pnl: 0,
            unrealized_pnl: 12,
            opened_at: "2026-04-10T00:00:00Z"
          }
        ],
        recent_fills: [
          {
            id: "f1",
            symbol: "EURUSD",
            side: "open",
            quantity: 1,
            price: 1.1,
            event_time: "2026-04-10T00:00:00Z"
          }
        ]
      }
    });
  });

  await page.route("**/api/control/paper/signal", async (route) => {
    await route.fulfill({
      json: {
        account: {
          name: "default",
          currency: "USD",
          cash: 99990,
          equity: 100130,
          status: "active",
          last_mark_to_market_at: "2026-04-10T00:01:00Z"
        },
        open_positions: [],
        recent_fills: []
      }
    });
  });

  await page.goto("/paper-trading");
  await expect(page.getByText("EURUSD")).toBeVisible();
  await page.getByRole("button", { name: /submit signal/i }).click();
});
