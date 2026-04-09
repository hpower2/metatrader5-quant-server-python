const numberFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2
});

const compactFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 2
});

export function formatNumber(value: number, fractionDigits = 2): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: fractionDigits,
    minimumFractionDigits: Math.min(fractionDigits, 2)
  }).format(value);
}

export function formatCompactNumber(value: number): string {
  return compactFormatter.format(value);
}

export function formatPercent(value: number): string {
  return `${numberFormatter.format(value * 100)}%`;
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

