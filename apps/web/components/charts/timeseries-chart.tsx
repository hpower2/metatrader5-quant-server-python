"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState } from "@/components/shared/empty-state";

export function TimeSeriesChart({
  data,
  valueKey,
  stroke = "#1ecbe1"
}: {
  data: Array<Record<string, number | string>>;
  valueKey: string;
  stroke?: string;
}) {
  if (data.length === 0) {
    return <EmptyState title="No time series data" description="Run a workflow to populate this chart." />;
  }

  return (
    <div className="h-[20rem] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(120, 136, 153, 0.12)" vertical={false} />
          <XAxis dataKey="timestamp" hide />
          <YAxis stroke="#8ea0b5" width={50} />
          <Tooltip contentStyle={{ background: "#101720", border: "1px solid rgba(120,136,153,0.2)" }} />
          <Line dataKey={valueKey} stroke={stroke} type="monotone" strokeWidth={2.25} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

