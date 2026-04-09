"use client";

import { create } from "zustand";

type LayoutMode = "expanded" | "compact";
type CandleOverlay = "none" | "rsi" | "atr";

interface UiState {
  sidebarOpen: boolean;
  layoutMode: LayoutMode;
  candleOverlay: CandleOverlay;
  setSidebarOpen: (open: boolean) => void;
  setLayoutMode: (mode: LayoutMode) => void;
  setCandleOverlay: (overlay: CandleOverlay) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  layoutMode: "expanded",
  candleOverlay: "none",
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setLayoutMode: (layoutMode) => set({ layoutMode }),
  setCandleOverlay: (candleOverlay) => set({ candleOverlay })
}));

