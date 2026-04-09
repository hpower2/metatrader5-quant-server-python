"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState } from "@/components/shared/empty-state";

export function VolumeChart({ data }: { data: Array<Record<string, number | string>> }) {
  if (data.length === 0) {
    return <EmptyState title="No volume profile" description="Volume will appear once candles are loaded." />;
  }

  return (
    <div className="h-[12rem] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid stroke="rgba(120, 136, 153, 0.12)" vertical={false} />
          <XAxis dataKey="timestamp" hide />
          <YAxis stroke="#8ea0b5" width={50} />
          <Tooltip contentStyle={{ background: "#101720", border: "1px solid rgba(120,136,153,0.2)" }} />
          <Bar dataKey="volume" fill="#ff9b35" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

