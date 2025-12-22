import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Home from "./page";

// Mock the api module
vi.mock("@/lib/api", () => ({
  checkHealth: vi.fn().mockResolvedValue({ status: "healthy", service: "Adaptive Professor" }),
  startLecture: vi.fn(),
}));

import { startLecture } from "@/lib/api";

describe("Home", () => {
  it("renders the title", () => {
    render(<Home />);
    expect(screen.getByText("Adaptive Professor")).toBeInTheDocument();
  });

  it("renders the topic input", () => {
    render(<Home />);
    expect(screen.getByPlaceholderText(/Enter a topic/)).toBeInTheDocument();
  });

  it("renders the start lecture button", () => {
    render(<Home />);
    expect(screen.getByText("Start Lecture")).toBeInTheDocument();
  });

  it("disables button when topic is empty", () => {
    render(<Home />);
    const button = screen.getByText("Start Lecture");
    expect(button).toBeDisabled();
  });

  it("enables button when topic is entered", () => {
    render(<Home />);
    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Rust" } });

    const button = screen.getByText("Start Lecture");
    expect(button).not.toBeDisabled();
  });

  it("displays slide when lecture starts successfully", async () => {
    vi.mocked(startLecture).mockResolvedValue({
      type: "render_slide",
      slide_id: "slide_01",
      layout: "title",
      content: {
        title: "Welcome to: Test Topic",
        text: "Let's begin our learning journey.",
      },
      interactive_controls: [{ label: "Next", action: "advance" }],
      allow_freeform_input: true,
    });

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test Topic" } });

    const button = screen.getByText("Start Lecture");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Welcome to: Test Topic")).toBeInTheDocument();
    });
  });

  it("displays error when lecture fails to start", async () => {
    vi.mocked(startLecture).mockRejectedValue(new Error("Network error"));

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test" } });

    const button = screen.getByText("Start Lecture");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });
});
