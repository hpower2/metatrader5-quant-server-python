export const queryKeys = {
  health: ["health"] as const,
  syncStatus: ["sync-status"] as const,
  symbols: ["symbols"] as const,
  candles: (symbol: string, timeframe: string, limit: number) => ["candles", symbol, timeframe, limit] as const,
  paperStatus: (accountName: string) => ["paper-status", accountName] as const
};

