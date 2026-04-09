"use client";

import { useMutation } from "@tanstack/react-query";

import { buildDataset } from "@/lib/api/queries";
import type { DatasetBuildRequest } from "@/features/datasets/schemas/dataset-form";

export function useDatasetBuild() {
  return useMutation({
    mutationFn: (payload: DatasetBuildRequest) => buildDataset(payload)
  });
}
