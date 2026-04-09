"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function SymbolSelector({
  value,
  onValueChange,
  options
}: {
  value: string;
  onValueChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
}) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="min-w-[11rem]">
        <SelectValue placeholder="Select symbol" />
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

