"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { timeframeOptions } from "@/lib/constants/options";

export function TimeframeSelector({
  value,
  onValueChange
}: {
  value: string;
  onValueChange: (value: string) => void;
}) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="min-w-[7rem]">
        <SelectValue placeholder="Timeframe" />
      </SelectTrigger>
      <SelectContent>
        {timeframeOptions.map((option) => (
          <SelectItem key={option} value={option}>
            {option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
