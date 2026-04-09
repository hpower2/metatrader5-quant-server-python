import { expect, test } from "@playwright/test";

test("dataset build flow", async ({ page }) => {
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

  await page.route("**/api/control/datasets/build", async (route) => {
    await route.fulfill({
      json: {
        artifact_dir: "/tmp/dataset",
        dataset_rows: 1000,
        train_rows: 700,
        validation_rows: 150,
        test_rows: 150,
        walk_forward_slices: [{ train_start: 0, train_end: 700, validation_end: 850, test_end: 1000 }]
      }
    });
  });

  await page.goto("/datasets");
  await page.locator('input[name="dataset_name"]').fill("eurusd_dataset");
  await page.getByRole("button", { name: /build dataset/i }).click();

  await expect(page.getByText("/tmp/dataset")).toBeVisible();
});

