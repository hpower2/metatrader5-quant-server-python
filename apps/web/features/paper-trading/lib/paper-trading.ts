import type { PaperAccountStatus } from "@/types/api";
import type { PaperSignalRequest, PaperSignalValues } from "@/features/paper-trading/schemas/paper-signal-form";

export function toPaperSignalRequest(values: PaperSignalValues): PaperSignalRequest {
  return {
    account_name: values.account_name,
    symbol: values.symbol,
    side: Number(values.side),
    quantity: values.quantity,
    stop_loss: values.stop_loss,
    take_profit: values.take_profit
  };
}

export function buildRiskWarnings(status?: PaperAccountStatus | null) {
  if (!status) {
    return [];
  }

  const warnings: Array<{ title: string; description: string; severity: string }> = [];
  const totalUnrealized = status.open_positions.reduce((sum, position) => sum + position.unrealized_pnl, 0);
  const concentration = status.open_positions.reduce<Record<string, number>>((acc, position) => {
    acc[position.symbol] = (acc[position.symbol] ?? 0) + 1;
    return acc;
  }, {});

  if (totalUnrealized < 0) {
    warnings.push({
      title: "Negative open PnL",
      description: `Open positions are carrying ${totalUnrealized.toFixed(2)} in unrealized losses.`,
      severity: "warning"
    });
  }

  Object.entries(concentration).forEach(([symbol, count]) => {
    if (count > 1) {
      warnings.push({
        title: "Symbol concentration",
        description: `${symbol} currently has ${count} open paper positions.`,
        severity: "info"
      });
    }
  });

  return warnings;
}
