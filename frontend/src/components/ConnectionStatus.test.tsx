import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConnectionStatus } from "./ConnectionStatus";

// Mock the api module
vi.mock("@/lib/api", () => ({
  checkHealth: vi.fn(),
}));

import { checkHealth } from "@/lib/api";

describe("ConnectionStatus", () => {
  it("shows checking state initially", () => {
    vi.mocked(checkHealth).mockImplementation(() => new Promise(() => {}));
    render(<ConnectionStatus />);
    expect(screen.getByText("Checking...")).toBeInTheDocument();
  });

  it("shows connected when health check succeeds", async () => {
    vi.mocked(checkHealth).mockResolvedValue({
      status: "healthy",
      service: "Adaptive Professor",
    });

    render(<ConnectionStatus />);

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });
  });

  it("shows disconnected when health check fails", async () => {
    vi.mocked(checkHealth).mockRejectedValue(new Error("Network error"));

    render(<ConnectionStatus />);

    await waitFor(() => {
      expect(screen.getByText("Disconnected")).toBeInTheDocument();
    });
  });
});
