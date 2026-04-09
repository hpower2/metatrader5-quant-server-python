"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { DataTable } from "@/components/shared/data-table";
import { FormFeedback } from "@/components/shared/form-feedback";
import { FormFieldShell } from "@/components/shared/form-field-shell";
import { PageHeader } from "@/components/shared/page-header";
import { SectionShell } from "@/components/shared/section-shell";
import { SymbolSelector } from "@/components/shared/symbol-selector";
import { TimeframeSelector } from "@/components/shared/timeframe-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatNumber } from "@/lib/formatters";
import { useSymbolOptions } from "@/hooks/use-symbol-options";
import { toDatasetBuildRequest } from "@/features/datasets/lib/dataset-build";
import { datasetFormSchema } from "@/features/datasets/schemas/dataset-form";
import { useDatasetBuild } from "@/features/datasets/hooks/use-dataset-build";

export function DatasetsPage() {
  const symbolsQuery = useSymbolOptions();
  const mutation = useDatasetBuild();
  const form = useForm<z.input<typeof datasetFormSchema>, unknown, z.output<typeof datasetFormSchema>>({
    resolver: zodResolver(datasetFormSchema),
    defaultValues: {
      dataset_name: "eurusd_m1_train70000_test10000",
      symbol: "EURUSD",
      timeframe: "M1",
      total_bars: 80000,
      higher_timeframe: "M5",
      feature_windows: "5,14,20,50",
      horizon_bars: 5,
      return_threshold: 0.0005,
      train_bars: 70000,
      validation_bars: 0,
      test_bars: 0,
      train_ratio: 0.7,
      validation_ratio: 0.15,
      test_ratio: 0.15,
      walk_forward_train_bars: 2000,
      walk_forward_validation_bars: 500,
      walk_forward_test_bars: 500,
      walk_forward_step_bars: 500
    }
  });
  const higherTimeframe = form.watch("higher_timeframe");
  const higherTimeframeValue = typeof higherTimeframe === "string" && higherTimeframe.length > 0 ? higherTimeframe : "M5";

  const onSubmit = form.handleSubmit((values) => mutation.mutate(toDatasetBuildRequest(values)));

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dataset workflows"
        title="Dataset builder"
        description="Configure symbol, timeframe, explicit train/test bar windows, and label horizon, then build a persisted research dataset artifact."
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionShell title="Build configuration" description="Validated dataset configuration with explicit split controls.">
          <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
            <FormFeedback
              className="md:col-span-2"
              message={mutation.error instanceof Error ? mutation.error.message : null}
            />
            <FormFieldShell
              label="Dataset name"
              htmlFor="dataset_name"
              error={form.formState.errors.dataset_name?.message}
              description="Stable artifact identifier used for persisted dataset exports."
            >
              <Input id="dataset_name" {...form.register("dataset_name")} />
            </FormFieldShell>
            <FormFieldShell label="Symbol" description="Primary instrument for the dataset window.">
              <SymbolSelector value={form.watch("symbol")} onValueChange={(value) => form.setValue("symbol", value)} options={symbolsQuery.options} />
            </FormFieldShell>
            <FormFieldShell label="Timeframe" description="Base bar resolution for the dataset.">
              <TimeframeSelector value={form.watch("timeframe")} onValueChange={(value) => form.setValue("timeframe", value)} />
            </FormFieldShell>
            <FormFieldShell
              label="Total bars"
              htmlFor="total_bars"
              error={form.formState.errors.total_bars?.message}
              description="Total bars fetched first, before split allocation (example: 80000)."
            >
              <Input id="total_bars" type="number" step="1000" {...form.register("total_bars")} />
            </FormFieldShell>
            <FormFieldShell label="Higher timeframe" description="Optional higher timeframe join for multi-timeframe features.">
              <TimeframeSelector value={higherTimeframeValue} onValueChange={(value) => form.setValue("higher_timeframe", value)} />
            </FormFieldShell>
            <FormFieldShell
              label="Feature windows"
              htmlFor="feature_windows"
              error={form.formState.errors.feature_windows?.message}
              description="Comma-separated rolling windows to engineer into the dataset."
            >
              <Input id="feature_windows" {...form.register("feature_windows")} />
            </FormFieldShell>
            <FormFieldShell
              label="Horizon bars"
              htmlFor="horizon_bars"
              error={form.formState.errors.horizon_bars?.message}
              description="Forward return horizon used by the labeler."
            >
              <Input id="horizon_bars" type="number" step="1" {...form.register("horizon_bars")} />
            </FormFieldShell>
            <FormFieldShell
              label="Return threshold"
              htmlFor="return_threshold"
              error={form.formState.errors.return_threshold?.message}
              description="Minimum forward return required to classify a positive label."
            >
              <Input id="return_threshold" type="number" step="0.0001" {...form.register("return_threshold")} />
            </FormFieldShell>
            <FormFieldShell
              label="Train bars"
              htmlFor="train_bars"
              error={form.formState.errors.train_bars?.message}
              description="Exact number of rows allocated to the training split."
            >
              <Input id="train_bars" type="number" step="1000" {...form.register("train_bars")} />
            </FormFieldShell>
            <FormFieldShell
              label="Validation bars"
              htmlFor="validation_bars"
              error={form.formState.errors.validation_bars?.message}
              description="Optional validation rows. Use 0 to skip validation split."
            >
              <Input id="validation_bars" type="number" step="500" {...form.register("validation_bars")} />
            </FormFieldShell>
            <FormFieldShell
              label="Test bars"
              htmlFor="test_bars"
              error={form.formState.errors.test_bars?.message}
              description="Held-out testing rows. Set 0 to auto-allocate the full remainder."
            >
              <Input id="test_bars" type="number" step="500" {...form.register("test_bars")} />
            </FormFieldShell>
            <FormFieldShell
              label="Train ratio"
              htmlFor="train_ratio"
              error={form.formState.errors.train_ratio?.message}
              description="Fallback ratio mode if split bars are not provided."
            >
              <Input id="train_ratio" type="number" step="0.05" {...form.register("train_ratio")} />
            </FormFieldShell>
            <FormFieldShell
              label="Validation ratio"
              htmlFor="validation_ratio"
              error={form.formState.errors.validation_ratio?.message}
              description="Portion reserved for model selection and tuning."
            >
              <Input id="validation_ratio" type="number" step="0.05" {...form.register("validation_ratio")} />
            </FormFieldShell>
            <FormFieldShell
              label="Test ratio"
              htmlFor="test_ratio"
              error={form.formState.errors.test_ratio?.message}
              description="Held-out evaluation slice. Ratios must sum to 1."
            >
              <Input id="test_ratio" type="number" step="0.05" {...form.register("test_ratio")} />
            </FormFieldShell>
            <FormFieldShell
              label="WF train bars"
              htmlFor="walk_forward_train_bars"
              error={form.formState.errors.walk_forward_train_bars?.message}
              description="Walk-forward training window length."
            >
              <Input id="walk_forward_train_bars" type="number" step="50" {...form.register("walk_forward_train_bars")} />
            </FormFieldShell>
            <FormFieldShell
              label="WF validation bars"
              htmlFor="walk_forward_validation_bars"
              error={form.formState.errors.walk_forward_validation_bars?.message}
              description="Walk-forward validation window length."
            >
              <Input
                id="walk_forward_validation_bars"
                type="number"
                step="50"
                {...form.register("walk_forward_validation_bars")}
              />
            </FormFieldShell>
            <FormFieldShell
              label="WF test bars"
              htmlFor="walk_forward_test_bars"
              error={form.formState.errors.walk_forward_test_bars?.message}
              description="Walk-forward test window length."
            >
              <Input id="walk_forward_test_bars" type="number" step="50" {...form.register("walk_forward_test_bars")} />
            </FormFieldShell>
            <FormFieldShell
              label="WF step bars"
              htmlFor="walk_forward_step_bars"
              error={form.formState.errors.walk_forward_step_bars?.message}
              description="Stride between successive walk-forward slices."
            >
              <Input id="walk_forward_step_bars" type="number" step="25" {...form.register("walk_forward_step_bars")} />
            </FormFieldShell>
            <div className="md:col-span-2">
              <FormFeedback
                tone="success"
                message={mutation.data ? `Dataset built successfully at ${mutation.data.artifact_dir}.` : null}
              />
            </div>
            <div className="md:col-span-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Building dataset..." : "Build dataset"}
              </Button>
            </div>
          </form>
        </SectionShell>

        <SectionShell title="Result summary" description="Artifact metadata returned by the dataset workflow.">
          {mutation.data ? (
            <DataTable
              data={[
                { key: "Artifact dir", value: mutation.data.artifact_dir },
                { key: "Dataset rows", value: formatNumber(mutation.data.dataset_rows, 0) },
                { key: "Train rows", value: formatNumber(mutation.data.train_rows, 0) },
                { key: "Validation rows", value: formatNumber(mutation.data.validation_rows, 0) },
                { key: "Test rows", value: formatNumber(mutation.data.test_rows, 0) },
                { key: "Walk-forward slices", value: formatNumber(mutation.data.walk_forward_slices.length, 0) }
              ]}
              columns={[
                { key: "key", header: "Metric", cell: (row) => row.key },
                { key: "value", header: "Value", cell: (row) => row.value }
              ]}
            />
          ) : (
            <p className="text-sm text-muted-foreground">Run the builder to inspect split sizes and artifact location.</p>
          )}
        </SectionShell>
      </div>
    </div>
  );
}
