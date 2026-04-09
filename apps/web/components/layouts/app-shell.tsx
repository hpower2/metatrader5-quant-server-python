"use client";

import Link from "next/link";
import { Menu, PanelsTopLeft } from "lucide-react";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { navigationItems } from "@/lib/constants/navigation";
import { cn } from "@/lib/utils/cn";
import { useUiStore } from "@/stores/ui-store";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { sidebarOpen, setSidebarOpen } = useUiStore();

  return (
    <div className="surface-grid min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-[1800px] gap-4 px-4 py-4 lg:px-6">
        <aside
          className={cn(
            "panel-shadow hidden w-72 shrink-0 rounded-2xl border border-border/70 bg-card/85 p-4 backdrop-blur-md lg:block",
            !sidebarOpen && "lg:w-24"
          )}
        >
          <div className="flex items-center justify-between gap-3 border-b border-border/60 pb-4">
            <div className={cn("overflow-hidden transition", !sidebarOpen && "w-0 opacity-0")}>
              <p className="text-xs uppercase tracking-[0.25em] text-primary">Quant Ops</p>
              <h1 className="font-semibold">MT5 Research Console</h1>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <PanelsTopLeft className="h-4 w-4" />
            </Button>
          </div>
          <nav className="mt-6 space-y-1">
            {navigationItems.map((item) => {
              const active = pathname.startsWith(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                    active ? "bg-primary/14 text-primary" : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className={cn(!sidebarOpen && "hidden")}>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="panel-shadow mb-4 flex items-center justify-between rounded-2xl border border-border/70 bg-card/80 px-4 py-3 backdrop-blur-md lg:px-5">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-primary">Internal trading platform</p>
              <h2 className="text-lg font-semibold">Research, ingestion, and paper execution</h2>
            </div>
            <Button variant="outline" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <Menu className="mr-2 h-4 w-4" />
              Menu
            </Button>
          </header>
          <main className="flex-1 pb-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
