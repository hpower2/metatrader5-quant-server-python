import type { DatasetBuildRequest, DatasetFormValues } from "@/features/datasets/schemas/dataset-form";

export function parseFeatureWindows(value: string) {
  return value
    .split(",")
    .map((part) => Number(part.trim()))
    .filter((part) => Number.isFinite(part) && part > 0);
}

export function toDatasetBuildRequest(values: DatasetFormValues): DatasetBuildRequest {
  const windows = parseFeatureWindows(values.feature_windows);

  return {
    dataset_name: values.dataset_name,
    symbol: values.symbol,
    timeframe: values.timeframe,
    total_bars: values.total_bars,
    higher_timeframe: values.higher_timeframe ?? null,
    split: {
      train_ratio: values.train_ratio,
      validation_ratio: values.validation_ratio,
      test_ratio: values.test_ratio,
      train_bars: values.train_bars,
      validation_bars: values.validation_bars,
      test_bars: values.test_bars > 0 ? values.test_bars : null
    },
    walk_forward: {
      train_bars: values.walk_forward_train_bars,
      validation_bars: values.walk_forward_validation_bars,
      test_bars: values.walk_forward_test_bars,
      step_bars: values.walk_forward_step_bars
    },
    feature_config: {
      windows,
      add_multi_timeframe: Boolean(values.higher_timeframe)
    },
    label_config: {
      horizon_bars: values.horizon_bars,
      return_threshold: values.return_threshold
    }
  };
}
