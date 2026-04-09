import { describe, expect, it } from "vitest";

import { statusToneFromValue } from "@/lib/utils/status";

describe("statusToneFromValue", () => {
  it("maps success values", () => {
    expect(statusToneFromValue("healthy")).toBe("success");
  });

  it("maps error values", () => {
    expect(statusToneFromValue("failed")).toBe("error");
  });
});
