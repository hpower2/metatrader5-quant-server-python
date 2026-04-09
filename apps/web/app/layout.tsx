import type { Metadata } from "next";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";

import { AppShell } from "@/components/layouts/app-shell";
import { AppQueryProvider } from "@/lib/query/providers";
import "@/styles/globals.css";

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"]
});

const displayFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "700"]
});

export const metadata: Metadata = {
  title: "MT5 Quant Console",
  description: "Internal dashboard for ingestion, datasets, backtests, and paper trading."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${bodyFont.variable} ${displayFont.variable} font-sans antialiased`}>
        <AppQueryProvider>
          <AppShell>{children}</AppShell>
        </AppQueryProvider>
      </body>
    </html>
  );
}

