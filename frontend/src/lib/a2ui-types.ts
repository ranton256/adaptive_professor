/**
 * A2UI Core Type Definitions.
 * Strict TypeScript mirror of the Python A2UI definitions.
 */

export type A2UIAction = {
  type: "action";
  name: string;
  parameters: Record<string, unknown>;
};

export type BaseComponent = {
  id?: string;
  style?: React.CSSProperties;
};

export type TextComponent = BaseComponent & {
  type: "text";
  content: string;
  variant: "h1" | "h2" | "h3" | "body" | "caption";
};

export type MarkdownComponent = BaseComponent & {
  type: "markdown";
  content: string;
};

export type ButtonComponent = BaseComponent & {
  type: "button";
  label: string;
  action: A2UIAction;
  variant: "primary" | "secondary" | "outline" | "ghost" | "danger";
  disabled?: boolean;
};

export type ContainerComponent = BaseComponent & {
  type: "container";
  layout: "vertical" | "horizontal" | "grid";
  children: Component[];
};

export type CodeComponent = BaseComponent & {
  type: "code";
  code: string;
  language: string;
  show_line_numbers?: boolean;
};

export type ImageComponent = BaseComponent & {
  type: "image";
  src: string;
  alt: string;
  caption?: string;
};

export type ConceptMapComponent = BaseComponent & {
  type: "concept_map";
  mermaid_code?: string;
  json_data?: string;
};

export type CodeExecutionComponent = BaseComponent & {
  type: "code_execution";
  code: string;
  language: string;
};

export type Component =
  | TextComponent
  | MarkdownComponent
  | ButtonComponent
  | ContainerComponent
  | CodeComponent
  | ImageComponent
  | ConceptMapComponent
  | CodeExecutionComponent;

export type A2UIMessage = {
  type: "render";
  root: Component;
  meta: {
    session_id: string;
    slide_index: number;
    total_slides: number;
    slide_id: string;
    layout: string;
    [key: string]: unknown;
  };
};
