"use client";

import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeHighlight from "rehype-highlight";
import mermaid from "mermaid";
import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";
import { CodeExecutor } from "./CodeExecutor";

/**
 * Recursively extract text content from React children.
 * This handles the case where rehype-highlight has transformed
 * code into nested span elements for syntax highlighting.
 */
function extractTextFromChildren(children: React.ReactNode): string {
  if (typeof children === "string") return children;
  if (typeof children === "number") return String(children);
  if (!children) return "";
  if (Array.isArray(children)) {
    return children.map(extractTextFromChildren).join("");
  }
  if (React.isValidElement(children)) {
    const props = children.props as { children?: React.ReactNode };
    return extractTextFromChildren(props.children);
  }
  return "";
}

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  fontFamily: "inherit",
  mindmap: {
    padding: 20,
    useMaxWidth: false,
  },
  flowchart: {
    useMaxWidth: false,
    padding: 20,
  },
});

interface MermaidDiagramProps {
  code: string;
  onNodeClick?: (concept: string) => void;
}

function MermaidDiagram({ code, onNodeClick }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current) return;

      try {
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
        const { svg } = await mermaid.render(id, code);
        setSvg(svg);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to render diagram");
        console.error("Mermaid rendering error:", err);
      }
    };

    renderDiagram();
  }, [code]);

  // Fix SVG viewBox to prevent clipping and attach click handlers
  useEffect(() => {
    if (!containerRef.current || !svg) return;

    const container = containerRef.current;
    const svgElement = container.querySelector("svg");

    // Fix SVG to prevent clipping
    if (svgElement) {
      svgElement.style.overflow = "visible";
      svgElement.style.maxWidth = "none";

      // Expand viewBox if it exists to add padding
      const viewBox = svgElement.getAttribute("viewBox");
      if (viewBox) {
        const [x, y, width, height] = viewBox.split(" ").map(Number);
        // Add padding to viewBox to prevent text clipping
        const padding = 40;
        svgElement.setAttribute(
          "viewBox",
          `${x - padding} ${y - padding} ${width + padding * 2} ${height + padding * 2}`
        );
      }
    }

    // Attach click handlers if callback provided
    if (!onNodeClick) return;

    // Find all text elements and their parent groups in the mindmap
    const nodes = container.querySelectorAll(".mindmap-node, .node, g[class*='node']");

    nodes.forEach((node) => {
      const textElement = node.querySelector("text, .nodeLabel");
      if (textElement) {
        const concept = textElement.textContent?.trim();
        if (concept) {
          // Style as clickable
          (node as HTMLElement).style.cursor = "pointer";

          // Add hover effect
          node.addEventListener("mouseenter", () => {
            (node as HTMLElement).style.opacity = "0.7";
          });
          node.addEventListener("mouseleave", () => {
            (node as HTMLElement).style.opacity = "1";
          });

          // Add click handler
          node.addEventListener("click", (e) => {
            e.stopPropagation();
            onNodeClick(concept);
          });
        }
      }
    });

    // Cleanup
    return () => {
      nodes.forEach((node) => {
        node.replaceWith(node.cloneNode(true));
      });
    };
  }, [svg, onNodeClick]);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.25));
  const handleResetZoom = () => setZoom(1);

  if (error) {
    return (
      <div className="my-4 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-900/20">
        <p className="font-semibold text-amber-800 dark:text-amber-200">
          Diagram could not be rendered
        </p>
        <details className="mt-2">
          <summary className="cursor-pointer text-sm text-amber-700 dark:text-amber-300">
            Show diagram code
          </summary>
          <pre className="mt-2 overflow-x-auto rounded bg-zinc-100 p-2 text-xs text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200">
            {code}
          </pre>
        </details>
      </div>
    );
  }

  return (
    <div className="my-4 rounded-lg bg-zinc-100 dark:bg-zinc-800">
      {/* Zoom controls */}
      <div className="flex items-center justify-between border-b border-zinc-200 px-3 py-2 dark:border-zinc-700">
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          Zoom: {Math.round(zoom * 100)}%
        </span>
        <div className="flex gap-1">
          <button
            onClick={handleZoomOut}
            className="rounded bg-zinc-200 px-2 py-1 text-xs hover:bg-zinc-300 dark:bg-zinc-700 dark:hover:bg-zinc-600"
          >
            −
          </button>
          <button
            onClick={handleResetZoom}
            className="rounded bg-zinc-200 px-2 py-1 text-xs hover:bg-zinc-300 dark:bg-zinc-700 dark:hover:bg-zinc-600"
          >
            Reset
          </button>
          <button
            onClick={handleZoomIn}
            className="rounded bg-zinc-200 px-2 py-1 text-xs hover:bg-zinc-300 dark:bg-zinc-700 dark:hover:bg-zinc-600"
          >
            +
          </button>
        </div>
      </div>
      {/* Scrollable diagram container */}
      <div className="overflow-auto p-4" style={{ maxHeight: "70vh" }}>
        <div
          ref={containerRef}
          className="flex min-w-max justify-center transition-transform duration-200 [&_svg]:overflow-visible [&_svg]:max-w-none"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "top center",
            padding: "20px", // Extra padding to prevent edge clipping
          }}
          dangerouslySetInnerHTML={{ __html: svg }}
        />
      </div>
      {/* Hint for clickable nodes */}
      {onNodeClick && (
        <div className="border-t border-zinc-200 px-3 py-2 text-center text-xs text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
          Click any concept to explore it in depth
        </div>
      )}
    </div>
  );
}

interface MarkdownContentProps {
  content: string;
  onConceptClick?: (concept: string) => void;
}

export function MarkdownContent({ content, onConceptClick }: MarkdownContentProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex, rehypeHighlight]}
      components={{
        // Handle code blocks - detect mermaid
        pre: ({ children }) => {
          return (
            <pre className="my-4 overflow-x-auto rounded-lg bg-zinc-900 p-4 text-sm">
              {children}
            </pre>
          );
        },
        // Style code - detect mermaid and executable code blocks
        code: ({ children, className }) => {
          const match = /language-(\w+)/.exec(className || "");
          const language = match ? match[1] : "";
          // Extract raw text from children (handles syntax-highlighted spans)
          const codeString = extractTextFromChildren(children).replace(/\n$/, "");

          // Render mermaid diagrams with click support
          if (language === "mermaid") {
            return <MermaidDiagram code={codeString} onNodeClick={onConceptClick} />;
          }

          // Execute JavaScript/TypeScript code that contains chartConfig
          if (
            (language === "javascript" ||
              language === "js" ||
              language === "typescript" ||
              language === "ts") &&
            codeString.includes("chartConfig")
          ) {
            return <CodeExecutor code={codeString} language={language} />;
          }

          // Inline code (no language class)
          const isInline = !className;
          if (isInline) {
            return (
              <code className="rounded bg-zinc-200 px-1.5 py-0.5 font-mono text-sm dark:bg-zinc-700">
                {children}
              </code>
            );
          }

          // Regular code block
          return <code className={className}>{children}</code>;
        },
        // Style paragraphs
        p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
        // Style lists
        ul: ({ children }) => <ul className="mb-4 ml-6 list-disc space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="mb-4 ml-6 list-decimal space-y-1">{children}</ol>,
        // Style headings
        h1: ({ children }) => <h1 className="mb-4 text-2xl font-bold">{children}</h1>,
        h2: ({ children }) => <h2 className="mb-3 text-xl font-bold">{children}</h2>,
        h3: ({ children }) => <h3 className="mb-2 text-lg font-semibold">{children}</h3>,
        // Style blockquotes
        blockquote: ({ children }) => (
          <blockquote className="my-4 border-l-4 border-blue-500 pl-4 italic text-zinc-600 dark:text-zinc-400">
            {children}
          </blockquote>
        ),
        // Style tables
        table: ({ children }) => (
          <div className="my-4 overflow-x-auto">
            <table className="min-w-full border-collapse border border-zinc-300 dark:border-zinc-700">
              {children}
            </table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-zinc-300 bg-zinc-100 px-4 py-2 text-left font-semibold dark:border-zinc-700 dark:bg-zinc-800">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-zinc-300 px-4 py-2 dark:border-zinc-700">{children}</td>
        ),
        // Style strong/bold
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        // Style links
        a: ({ href, children }) => (
          <a
            href={href}
            className="text-blue-600 underline hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
            target="_blank"
            rel="noopener noreferrer"
          >
            {children}
          </a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
