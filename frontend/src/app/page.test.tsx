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

const mockSlidePayload = {
  type: "render_slide",
  slide_id: "slide_01",
  session_id: "test-session-123",
  layout: "default",
  content: {
    title: "Introduction to Test Topic",
    text: "This is the first slide content.",
  },
  interactive_controls: [
    { label: "Next", action: "advance_main_thread" },
    { label: "Clarify", action: "clarify_slide" },
  ],
  allow_freeform_input: true,
  slide_index: 0,
  total_slides: 6,
};

const mockSecondSlide = {
  ...mockSlidePayload,
  slide_id: "slide_02",
  content: {
    title: "Second Slide",
    text: "This is the second slide content.",
  },
  interactive_controls: [
    { label: "Next", action: "advance_main_thread" },
    { label: "Previous", action: "go_previous" },
    { label: "Clarify", action: "clarify_slide" },
  ],
  slide_index: 1,
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
    vi.mocked(startLecture).mockResolvedValue(mockSlidePayload);

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test Topic" } });

    const button = screen.getByText("Start Lecture");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Introduction to Test Topic")).toBeInTheDocument();
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

  it("displays slide progress indicator", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockSlidePayload);

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.click(screen.getByText("Start Lecture"));

    await waitFor(() => {
      expect(screen.getByText("Slide 1 of 6")).toBeInTheDocument();
    });
  });

  it("displays interactive control buttons", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockSlidePayload);

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.click(screen.getByText("Start Lecture"));

    await waitFor(() => {
      expect(screen.getByText("Next")).toBeInTheDocument();
      expect(screen.getByText("Clarify")).toBeInTheDocument();
    });
  });

  it("advances to next slide when Next is clicked", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockSlidePayload);
    vi.mocked(performAction).mockResolvedValue(mockSecondSlide);

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

    expect(performAction).toHaveBeenCalledWith(
      "test-session-123",
      "advance_main_thread",
      undefined
    );
  });

  it("shows Previous button on second slide", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockSlidePayload);
    vi.mocked(performAction).mockResolvedValue(mockSecondSlide);

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.click(screen.getByText("Start Lecture"));

    await waitFor(() => {
      expect(screen.getByText("Next")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Next"));

    await waitFor(() => {
      expect(screen.getByText("Previous")).toBeInTheDocument();
    });
  });

  it("resets to topic input when Start new lecture is clicked", async () => {
    vi.mocked(startLecture).mockResolvedValue(mockSlidePayload);

    render(<Home />);

    const input = screen.getByPlaceholderText(/Enter a topic/);
    fireEvent.change(input, { target: { value: "Test" } });
    fireEvent.click(screen.getByText("Start Lecture"));

    await waitFor(() => {
      expect(screen.getByText("Introduction to Test Topic")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("New lecture"));

    expect(screen.getByPlaceholderText(/Enter a topic/)).toBeInTheDocument();
    expect(screen.getByText("Start Lecture")).toBeInTheDocument();
  });
});
