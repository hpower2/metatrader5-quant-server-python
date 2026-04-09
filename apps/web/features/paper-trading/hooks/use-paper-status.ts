"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getPaperStatus, submitPaperSignal } from "@/lib/api/queries";
import { queryKeys } from "@/lib/query/query-keys";
import type { PaperSignalRequest } from "@/features/paper-trading/schemas/paper-signal-form";

export function usePaperStatus(accountName: string) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: queryKeys.paperStatus(accountName),
    queryFn: () => getPaperStatus(accountName),
    refetchInterval: 5_000
  });

  const signalMutation = useMutation({
    mutationFn: (payload: PaperSignalRequest) => submitPaperSignal(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.paperStatus(accountName), data);
    }
  });

  return { query, signalMutation };
}
