import {
  Activity,
  BarChart3,
  CandlestickChart,
  Database,
  Layers3,
  ShieldCheck,
  Wallet
} from "lucide-react";

export const navigationItems = [
  { href: "/dashboard", label: "Dashboard", icon: Activity },
  { href: "/market-data", label: "Market Data", icon: CandlestickChart },
  { href: "/features-explorer", label: "Features", icon: Layers3 },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/backtests", label: "Backtests", icon: BarChart3 },
  { href: "/paper-trading", label: "Paper Trading", icon: Wallet },
  { href: "/admin", label: "Admin", icon: ShieldCheck }
] as const;

