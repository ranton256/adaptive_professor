import React from "react";
import { MarkdownContent } from "@/components/MarkdownContent";
import { ConceptMap, parseMermaidMindmap } from "@/components/ConceptMap";
import { CodeExecutor } from "@/components/CodeExecutor";

import {
  Component,
  ContainerComponent,
  ButtonComponent,
  TextComponent,
  MarkdownComponent as MarkdownComponentType,
  ConceptMapComponent,
  CodeExecutionComponent,
} from "./a2ui-types";

interface RendererProps {
  component: Component;
  onAction: (action: string, params: Record<string, unknown>) => void;
  // Callback for deep links or other specific interactions
  onConceptClick?: (concept: string) => void;
}

// Map A2UI variants to Tailwind classes
const TEXT_VARIANTS = {
  h1: "text-3xl font-bold text-zinc-900 dark:text-zinc-100",
  h2: "text-2xl font-bold text-zinc-900 dark:text-zinc-100",
  h3: "text-xl font-semibold text-zinc-900 dark:text-zinc-100",
  body: "text-base text-zinc-700 dark:text-zinc-300",
  caption: "text-sm text-zinc-500 dark:text-zinc-400",
};

const BUTTON_VARIANTS = {
  primary: "bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700",
  secondary:
    "bg-indigo-100 text-indigo-800 border border-indigo-300 hover:bg-indigo-200 dark:bg-indigo-900/50 dark:text-indigo-200 dark:border-indigo-700 dark:hover:bg-indigo-800/50",
  outline:
    "bg-teal-100 text-teal-800 border border-teal-300 hover:bg-teal-200 dark:bg-teal-900/50 dark:text-teal-200 dark:border-teal-700 dark:hover:bg-teal-800/50",
  ghost:
    "bg-zinc-200 text-zinc-700 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-600",
  danger:
    "bg-rose-100 text-rose-800 border border-rose-300 hover:bg-rose-200 dark:bg-rose-900/50 dark:text-rose-200 dark:border-rose-700 dark:hover:bg-rose-800/50",
};

function ContainerRenderer({
  component,
  onAction,
  onConceptClick,
}: RendererProps & { component: ContainerComponent }) {
  const style = {
    display: "flex",
    flexDirection: component.layout === "horizontal" ? ("row" as const) : ("column" as const),
    ...component.style,
  };

  return (
    <div style={style} className="w-full">
      {component.children.map((child, idx) => (
        <A2UIComponentRenderer
          key={idx}
          component={child}
          onAction={onAction}
          onConceptClick={onConceptClick}
        />
      ))}
    </div>
  );
}

function ButtonRenderer({ component, onAction }: RendererProps & { component: ButtonComponent }) {
  const baseStyle =
    "h-9 rounded-lg px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 md:h-10 md:px-4 md:text-base";
  const variantStyle = BUTTON_VARIANTS[component.variant] || BUTTON_VARIANTS.primary;

  return (
    <button
      onClick={() => onAction(component.action.name, component.action.parameters)}
      disabled={component.disabled}
      className={`${baseStyle} ${variantStyle}`}
      style={component.style}
    >
      {component.label}
    </button>
  );
}

function TextRenderer({ component }: RendererProps & { component: TextComponent }) {
  const className = TEXT_VARIANTS[component.variant] || TEXT_VARIANTS.body;
  return (
    <div className={className} style={component.style}>
      {component.content}
    </div>
  );
}

function MarkdownRenderer({
  component,
  onConceptClick,
}: RendererProps & { component: MarkdownComponentType }) {
  return (
    <div className="prose dark:prose-invert max-w-none" style={component.style}>
      <MarkdownContent content={component.content} onConceptClick={onConceptClick} />
    </div>
  );
}

function ConceptMapRenderer({
  component,
  onConceptClick,
}: RendererProps & { component: ConceptMapComponent }) {
  if (component.mermaid_code) {
    const data = parseMermaidMindmap(component.mermaid_code);
    if (data) {
      return <ConceptMap data={data} onNodeClick={onConceptClick} />;
    }
  }
  return <div className="text-red-500">Invalid Concept Map Data</div>;
}

function CodeExecutionRenderer({
  component,
}: RendererProps & { component: CodeExecutionComponent }) {
  return <CodeExecutor code={component.code} language={component.language} />;
}

export function A2UIComponentRenderer(props: RendererProps) {
  const { component } = props;

  switch (component.type) {
    case "container":
      return <ContainerRenderer {...props} component={component} />;
    case "button":
      return <ButtonRenderer {...props} component={component} />;
    case "text":
      return <TextRenderer {...props} component={component} />;
    case "markdown":
      return <MarkdownRenderer {...props} component={component} />;
    case "concept_map":
      return <ConceptMapRenderer {...props} component={component} />;
    case "code_execution":
      return <CodeExecutionRenderer {...props} component={component} />;
    // Add other components as needed (code, image)
    default:
      console.warn(`Unknown component type: ${(component as { type: string }).type}`);
      return null;
  }
}
