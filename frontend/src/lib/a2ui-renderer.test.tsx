import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { A2UIComponentRenderer } from "./a2ui-renderer";
import { A2UIMessage } from "./a2ui-types";
import React from "react";

// Mock complex components
vi.mock("@/components/CodeExecutor", () => ({
  CodeExecutor: ({ code }: { code: string }) => <div data-testid="code-executor">{code}</div>,
}));

vi.mock("@/components/ConceptMap", () => ({
  ConceptMap: () => <div data-testid="concept-map">Concept Map</div>,
  parseMermaidMindmap: () => ({ root: "root", branches: [] }),
}));

describe("A2UIComponentRenderer", () => {
  it("renders text components", () => {
    const component = {
      type: "text" as const,
      content: "Hello World",
      variant: "h1" as const,
    };

    render(<A2UIComponentRenderer component={component} onAction={() => {}} />);
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("renders buttons and handles actions", () => {
    const handleAction = vi.fn();
    const component = {
      type: "button" as const,
      label: "Click Me",
      action: {
        type: "action" as const,
        name: "test_action",
        parameters: { foo: "bar" },
      },
      variant: "primary" as const,
    };

    render(<A2UIComponentRenderer component={component} onAction={handleAction} />);

    const button = screen.getByText("Click Me");
    fireEvent.click(button);

    expect(handleAction).toHaveBeenCalledWith("test_action", { foo: "bar" });
  });

  it("renders containers recursively", () => {
    const component = {
      type: "container" as const,
      layout: "vertical" as const,
      children: [
        {
          type: "text" as const,
          content: "Child 1",
          variant: "body" as const,
        },
        {
          type: "text" as const,
          content: "Child 2",
          variant: "body" as const,
        },
      ],
    };

    render(<A2UIComponentRenderer component={component} onAction={() => {}} />);

    expect(screen.getByText("Child 1")).toBeInTheDocument();
    expect(screen.getByText("Child 2")).toBeInTheDocument();
  });

  it("renders concept maps", () => {
    const component = {
      type: "concept_map" as const,
      mermaid_code: "mindmap\n  root((Root))",
    };
    render(<A2UIComponentRenderer component={component} onAction={() => {}} />);
    expect(screen.getByTestId("concept-map")).toBeInTheDocument();
  });

  it("renders code execution", () => {
    const component = {
      type: "code_execution" as const,
      code: "console.log('test')",
      language: "javascript",
    };
    render(<A2UIComponentRenderer component={component} onAction={() => {}} />);
    expect(screen.getByTestId("code-executor")).toHaveTextContent("console.log('test')");
  });
});
