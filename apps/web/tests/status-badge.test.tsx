import { render, screen } from "@testing-library/react";

import { StatusBadge } from "@/components/shared/status-badge";

describe("StatusBadge", () => {
  it("renders the provided status value", () => {
    render(<StatusBadge value="healthy" />);

    expect(screen.getByText("healthy")).toBeInTheDocument();
  });
});

