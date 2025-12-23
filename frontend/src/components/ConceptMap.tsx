"use client";

import React from "react";

export interface ConceptNode {
  name: string;
  children?: ConceptNode[];
}

export interface ConceptMapData {
  root: string;
  branches: ConceptNode[];
}

interface ConceptMapProps {
  data: ConceptMapData;
  onNodeClick?: (concept: string) => void;
}

// Color palette for branches (will cycle through for different branches)
const branchColors = [
  { bg: "bg-purple-600", border: "border-purple-500", hover: "hover:bg-purple-500" },
  { bg: "bg-amber-600", border: "border-amber-500", hover: "hover:bg-amber-500" },
  { bg: "bg-emerald-600", border: "border-emerald-500", hover: "hover:bg-emerald-500" },
  { bg: "bg-rose-600", border: "border-rose-500", hover: "hover:bg-rose-500" },
  { bg: "bg-cyan-600", border: "border-cyan-500", hover: "hover:bg-cyan-500" },
  { bg: "bg-indigo-600", border: "border-indigo-500", hover: "hover:bg-indigo-500" },
  { bg: "bg-orange-600", border: "border-orange-500", hover: "hover:bg-orange-500" },
  { bg: "bg-teal-600", border: "border-teal-500", hover: "hover:bg-teal-500" },
];

interface NodeProps {
  node: ConceptNode;
  colorIndex: number;
  onNodeClick?: (concept: string) => void;
  isRoot?: boolean;
}

function ConceptNodeComponent({ node, colorIndex, onNodeClick, isRoot = false }: NodeProps) {
  const color = branchColors[colorIndex % branchColors.length];

  const handleClick = () => {
    if (onNodeClick) {
      onNodeClick(node.name);
    }
  };

  if (isRoot) {
    return (
      <button
        onClick={handleClick}
        className="rounded-full bg-zinc-600 px-6 py-4 text-center text-lg font-bold text-white shadow-lg transition-all hover:bg-zinc-500 hover:scale-105"
      >
        {node.name}
      </button>
    );
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        onClick={handleClick}
        className={`rounded-lg ${color.bg} ${color.hover} px-3 py-2 text-sm font-medium text-white shadow transition-all hover:scale-105`}
      >
        {node.name}
      </button>
      {node.children && node.children.length > 0 && (
        <div className="ml-4 flex flex-col gap-1 border-l-2 border-zinc-600 pl-3">
          {node.children.map((child, idx) => (
            <button
              key={idx}
              onClick={() => onNodeClick?.(child.name)}
              className="rounded bg-zinc-700 px-2 py-1 text-left text-xs text-zinc-200 transition-all hover:bg-zinc-600 hover:scale-105"
            >
              {child.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export function ConceptMap({ data, onNodeClick }: ConceptMapProps) {
  // Split branches into left and right sides for balanced layout
  const midpoint = Math.ceil(data.branches.length / 2);
  const leftBranches = data.branches.slice(0, midpoint);
  const rightBranches = data.branches.slice(midpoint);

  return (
    <div className="my-4 rounded-lg bg-zinc-800 p-6">
      {/* Main layout: left branches - center root - right branches */}
      <div className="flex items-center justify-center gap-8">
        {/* Left branches */}
        <div className="flex flex-col items-end gap-4">
          {leftBranches.map((branch, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <ConceptNodeComponent node={branch} colorIndex={idx} onNodeClick={onNodeClick} />
              {/* Connector line */}
              <div className="h-0.5 w-8 bg-zinc-600" />
            </div>
          ))}
        </div>

        {/* Center root node */}
        <ConceptNodeComponent
          node={{ name: data.root }}
          colorIndex={0}
          onNodeClick={onNodeClick}
          isRoot
        />

        {/* Right branches */}
        <div className="flex flex-col items-start gap-4">
          {rightBranches.map((branch, idx) => (
            <div key={idx} className="flex items-center gap-3">
              {/* Connector line */}
              <div className="h-0.5 w-8 bg-zinc-600" />
              <ConceptNodeComponent
                node={branch}
                colorIndex={midpoint + idx}
                onNodeClick={onNodeClick}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Click hint */}
      {onNodeClick && (
        <div className="mt-6 text-center text-xs text-zinc-500">
          Click any concept to explore it in depth
        </div>
      )}
    </div>
  );
}

/**
 * Parse Mermaid mindmap syntax into ConceptMapData structure.
 * This provides backward compatibility with existing content.
 */
export function parseMermaidMindmap(mermaidCode: string): ConceptMapData | null {
  try {
    const lines = mermaidCode.split("\n").filter((l) => l.trim());

    // Find root - look for root((text)) pattern
    let root = "Topic";
    const rootMatch = mermaidCode.match(/root\(\(([^)]+)\)\)/);
    if (rootMatch) {
      root = rootMatch[1];
    }

    // Parse branches - look for indented items after root
    const branches: ConceptNode[] = [];
    let currentBranch: ConceptNode | null = null;
    let inMindmap = false;

    for (const line of lines) {
      const trimmed = line.trim();

      if (trimmed === "mindmap") {
        inMindmap = true;
        continue;
      }

      if (!inMindmap) continue;
      if (trimmed.startsWith("root(")) continue;

      // Count indentation (each level is 2 spaces)
      const indent = line.search(/\S/);
      const level = Math.floor(indent / 2);

      // Clean the node name (remove any markdown formatting)
      const nodeName = trimmed.replace(/[`*_]/g, "").trim();
      if (!nodeName) continue;

      if (level <= 2) {
        // This is a main branch
        currentBranch = { name: nodeName, children: [] };
        branches.push(currentBranch);
      } else if (level > 2 && currentBranch) {
        // This is a sub-item
        currentBranch.children = currentBranch.children || [];
        currentBranch.children.push({ name: nodeName });
      }
    }

    return { root, branches };
  } catch {
    return null;
  }
}

/**
 * Parse JSON concept map data.
 */
export function parseJsonConceptMap(jsonStr: string): ConceptMapData | null {
  try {
    const data = JSON.parse(jsonStr);
    if (data.root && Array.isArray(data.branches)) {
      return data as ConceptMapData;
    }
    return null;
  } catch {
    return null;
  }
}
