"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Chart } from "react-chartjs-2";

// Register Chart.js components (zoom plugin registered dynamically on client)
ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Flag to track if zoom plugin is registered
let zoomPluginRegistered = false;

interface ChartConfig {
  type: "line" | "bar" | "pie" | "doughnut" | "scatter" | "bubble";
  data: {
    labels?: (string | number)[];
    datasets: Array<{
      label?: string;
      data: number[] | { x: number; y: number }[];
      backgroundColor?: string | string[];
      borderColor?: string | string[];
      tension?: number;
      fill?: boolean;
      [key: string]: unknown;
    }>;
  };
  options?: Record<string, unknown>;
}

interface ExecutionResult {
  chartConfig?: ChartConfig;
  logs: string[];
  error?: string;
}

interface CodeExecutorProps {
  code: string;
  language: string;
}

function executeCode(code: string): ExecutionResult {
  const logs: string[] = [];

  try {
    // Create custom console that captures output
    const customConsole = {
      log: (...args: unknown[]) => logs.push(args.map(String).join(" ")),
      warn: (...args: unknown[]) => logs.push(`[warn] ${args.map(String).join(" ")}`),
      error: (...args: unknown[]) => logs.push(`[error] ${args.map(String).join(" ")}`),
    };

    // Simple approach: just override console and return chartConfig
    // The code has access to normal JS globals (Math, Date, etc.) which are safe
    const fn = new Function(
      "console",
      `
      ${code}
      return typeof chartConfig !== 'undefined' ? chartConfig : undefined;
      `
    );

    const chartConfig = fn(customConsole) as ChartConfig | undefined;

    return {
      chartConfig,
      logs,
    };
  } catch (e) {
    return {
      logs,
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

export function CodeExecutor({ code, language }: CodeExecutorProps) {
  const [showCode, setShowCode] = useState(false);
  const [zoomReady, setZoomReady] = useState(false);
  const chartRef = useRef<ChartJS>(null);

  // Register zoom plugin dynamically on client side
  useEffect(() => {
    if (!zoomPluginRegistered && typeof window !== "undefined") {
      import("chartjs-plugin-zoom").then((zoomPlugin) => {
        ChartJS.register(zoomPlugin.default);
        zoomPluginRegistered = true;
        setZoomReady(true);
      });
    } else if (zoomPluginRegistered) {
      setZoomReady(true);
    }
  }, []);

  // Execute code synchronously via useMemo (no effect needed)
  const result = useMemo(() => executeCode(code), [code]);

  // Derive chart data and options from result
  const chartData = result.chartConfig?.data ?? null;
  const chartOptions = useMemo(() => {
    if (!result.chartConfig) return {};
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: true,
      ...result.chartConfig.options,
    };

    // Only add zoom plugin config if zoom is ready
    if (zoomReady) {
      return {
        ...baseOptions,
        plugins: {
          ...(result.chartConfig.options?.plugins as Record<string, unknown>),
          zoom: {
            pan: {
              enabled: true,
              mode: "xy" as const,
            },
            zoom: {
              wheel: {
                enabled: true,
              },
              pinch: {
                enabled: true,
              },
              mode: "xy" as const,
            },
          },
        },
      };
    }

    return baseOptions;
  }, [result, zoomReady]);

  const handleResetZoom = () => {
    if (chartRef.current) {
      chartRef.current.resetZoom();
    }
  };

  // Error state
  if (result.error) {
    return (
      <div className="my-4 rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-700 dark:bg-red-900/20">
        <p className="font-semibold text-red-800 dark:text-red-200">Code execution error</p>
        <pre className="mt-2 overflow-x-auto text-sm text-red-700 dark:text-red-300">
          {result.error}
        </pre>
        <details className="mt-3">
          <summary className="cursor-pointer text-sm text-red-700 hover:text-red-900 dark:text-red-300 dark:hover:text-red-100">
            Show code
          </summary>
          <pre className="mt-2 overflow-x-auto rounded bg-zinc-900 p-3 text-xs text-zinc-200">
            {code}
          </pre>
        </details>
      </div>
    );
  }

  // Chart output
  if (result.chartConfig && chartData) {
    return (
      <div className="my-4 space-y-2">
        <div className="rounded-lg bg-white p-4 dark:bg-zinc-800">
          <Chart
            ref={chartRef}
            type={result.chartConfig.type}
            data={chartData}
            options={chartOptions}
          />
          {zoomReady && (
            <div className="mt-2 flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400">
              <span>Scroll to zoom, drag to pan</span>
              <button
                onClick={handleResetZoom}
                className="rounded bg-zinc-200 px-2 py-1 hover:bg-zinc-300 dark:bg-zinc-700 dark:hover:bg-zinc-600"
              >
                Reset Zoom
              </button>
            </div>
          )}
        </div>

        {/* Console logs if any */}
        {result.logs.length > 0 && (
          <div className="rounded bg-zinc-900 p-3">
            <p className="mb-1 text-xs text-zinc-400">Console output:</p>
            {result.logs.map((log, i) => (
              <pre key={i} className="text-xs text-zinc-300">
                {log}
              </pre>
            ))}
          </div>
        )}

        {/* Toggle code view */}
        <button
          onClick={() => setShowCode(!showCode)}
          className="text-xs text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
        >
          {showCode ? "Hide code" : "Show code"}
        </button>
        {showCode && (
          <pre className="overflow-x-auto rounded bg-zinc-900 p-3 text-xs text-zinc-200">
            {code}
          </pre>
        )}
      </div>
    );
  }

  // Console output only (no chart)
  if (result.logs.length > 0) {
    return (
      <div className="my-4 space-y-2">
        <div className="rounded-lg bg-zinc-900 p-4">
          <p className="mb-2 text-xs text-zinc-400">Output:</p>
          {result.logs.map((log, i) => (
            <pre key={i} className="text-sm text-zinc-200">
              {log}
            </pre>
          ))}
        </div>
        <button
          onClick={() => setShowCode(!showCode)}
          className="text-xs text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
        >
          {showCode ? "Hide code" : "Show code"}
        </button>
        {showCode && (
          <pre className="overflow-x-auto rounded bg-zinc-900 p-3 text-xs text-zinc-200">
            {code}
          </pre>
        )}
      </div>
    );
  }

  // No output - just show code
  return (
    <div className="my-4">
      <pre className="overflow-x-auto rounded-lg bg-zinc-900 p-4 text-sm text-zinc-200">
        <code className={`language-${language}`}>{code}</code>
      </pre>
      <p className="mt-1 text-xs text-zinc-500">Code executed with no output</p>
    </div>
  );
}
