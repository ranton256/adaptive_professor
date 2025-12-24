import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import Home from "./page";

// Mock the api module
vi.mock("@/lib/api", () => ({
  checkHealth: vi.fn().mockResolvedValue({ status: "healthy", service: "Adaptive Professor" }),
  startLecture: vi.fn(),
  performAction: vi.fn(),
}));

import { startLecture, performAction } from "@/lib/api";
import { A2UIMessage } from "@/lib/a2ui-types";

const mockA2UIMessaage_Slide1 = {
  type: "render",
  meta: {
    session_id: "test-session-123",
    slide_index: 0,
    total_slides: 6,
    slide_id: "slide_01",
    layout: "default",
  },
  root: {
    type: "container",
    layout: "vertical",
    children: [
      {
        type: "text",
        content: "Introduction to Test Topic",
        variant: "h2",
      },
      {
        type: "markdown",
        content: "This is the first slide content.",
      },
      {
        type: "container",
        layout: "horizontal",
        children: [
          {
            type: "button",
            label: "Next",
            action: { type: "action", name: "advance_main_thread", parameters: {} },
            variant: "primary",
          },
          {
            type: "button",
            label: "Clarify",
            action: { type: "action", name: "clarify_slide", parameters: {} },
            variant: "secondary",
          },
        ],
      },
    ],
  },
};

const mockA2UIMessaage_Slide2 = {
  type: "render",
  meta: {
    session_id: "test-session-123",
    slide_index: 1,
    total_slides: 6,
    slide_id: "slide_02",
    layout: "default",
  },
  root: {
    type: "container",
    layout: "vertical",
    children: [
      {
        type: "text",
        content: "Second Slide",
        variant: "h2",
      },
      {
        type: "container",
        layout: "horizontal",
        children: [
          {
            type: "button",
            label: "Next",
            action: { type: "action", name: "advance_main_thread", parameters: {} },
            variant: "primary",
          },
          {
            type: "button",
            label: "Previous",
            action: { type: "action", name: "go_previous", parameters: {} },
            variant: "secondary",
          },
        ],
      },
    ],
  },
};

describe("Home", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the title", () => {
    render(<Home />);
    expect(screen.getByText("Adaptive Professor")).toBeInTheDocument();
  });

  it("renders the topic input", () => {
    render(<Home />);
    expect(screen.getByPlaceholderText(/Enter a topic/)).toBeInTheDocument();
  });

  it("displays slide when lecture starts successfully", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockA2UIMessaage_Slide1 as A2UIMessage);

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test Topic" } });

    const button = screen.getByText("Start Lecture");
    fireEvent.click(button);

    await waitFor(() => {
      // Look for the "h2" text component
      expect(screen.getByText("Introduction to Test Topic")).toBeInTheDocument();
      // Look for the "markdown" component content
      expect(screen.getByText("This is the first slide content.")).toBeInTheDocument();
      // Look for buttons
      expect(screen.getByText("Next")).toBeInTheDocument();
    });
  });

  it("advances to next slide when Next is clicked", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockA2UIMessaage_Slide1 as A2UIMessage);
    vi.mocked(performAction).mockResolvedValue(mockA2UIMessaage_Slide2 as A2UIMessage);

    render(<Home />);

    // Start lecture
    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.click(screen.getByText("Start Lecture"));

    await waitFor(() => {
      expect(screen.getByText("Next")).toBeInTheDocument();
    });

    // Click Next
    fireEvent.click(screen.getByText("Next"));

    await waitFor(() => {
      expect(screen.getByText("Second Slide")).toBeInTheDocument();
      expect(screen.getByText("Slide 2 of 6")).toBeInTheDocument();
    });

    // Verify action call
    expect(performAction).toHaveBeenCalledWith("test-session-123", "advance_main_thread", {});
  });
});
