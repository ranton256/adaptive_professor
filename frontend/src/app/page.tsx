"use client";

import { useState } from "react";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { A2UIComponentRenderer } from "@/lib/a2ui-renderer";
import { A2UIMessage } from "@/lib/a2ui-types";
import { startLecture, performAction } from "@/lib/api";

export default function Home() {
  const [topic, setTopic] = useState("");
  const [slide, setSlide] = useState<A2UIMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  async function handleStartLecture() {
    if (!topic.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const result = await startLecture(topic);
      setSlide(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start lecture");
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(action: string, params: Record<string, unknown> = {}) {
    if (!slide?.meta.session_id) return;

    setActionLoading(true);
    setError(null);
    try {
      const result = await performAction(slide.meta.session_id as string, action, params);
      setSlide(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setActionLoading(false);
    }
  }

  function handleReset() {
    setSlide(null);
    setTopic("");
    setError(null);
  }

  function handleConceptClick(concept: string) {
    // Trigger a deep dive when clicking on a concept in the mindmap or markdown
    handleAction("deep_dive", { concept });
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 font-sans dark:bg-zinc-900">
      <header className="flex items-center justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          Adaptive Professor
        </h1>
        <ConnectionStatus />
      </header>

      <main className="flex flex-1 flex-col items-center justify-center p-8">
        {!slide ? (
          <div className="w-full max-w-md space-y-4">
            <h2 className="text-center text-2xl font-bold text-zinc-900 dark:text-zinc-100">
              What would you like to learn?
            </h2>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter a topic (e.g., Rust Ownership)"
              className="w-full rounded-lg border border-zinc-300 px-4 py-3 text-zinc-900 placeholder:text-zinc-500 focus:border-blue-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100"
              onKeyDown={(e) => e.key === "Enter" && handleStartLecture()}
            />
            <button
              onClick={handleStartLecture}
              disabled={loading || !topic.trim()}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Starting..." : "Start Lecture"}
            </button>
            {error && <p className="text-center text-red-500">{error}</p>}
          </div>
        ) : (
          <div className="flex h-full w-full max-w-6xl flex-col px-4">
            {/* Progress indicator - fixed height */}
            <div className="flex-shrink-0 pb-4">
              <div className="flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
                <span className="font-medium">
                  Slide {(slide.meta.slide_index as number) + 1} of{" "}
                  {slide.meta.total_slides as number}
                </span>
                <button
                  onClick={handleReset}
                  className="text-sm text-zinc-500 underline hover:text-zinc-700 dark:hover:text-zinc-300"
                >
                  New lecture
                </button>
              </div>
              <div className="mt-2 h-2 rounded-full bg-zinc-200 dark:bg-zinc-700">
                <div
                  className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                  style={{
                    width: `${(((slide.meta.slide_index as number) + 1) / (slide.meta.total_slides as number)) * 100}%`,
                  }}
                />
              </div>
            </div>

            {/* Slide content - A2UI Rendered */}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <div className="rounded-xl bg-white p-6 shadow-lg dark:bg-zinc-800 md:p-8">
                {/* Reusing the card container, but content is now purely driven by A2UI */}
                <A2UIComponentRenderer
                  component={slide.root}
                  onAction={handleAction}
                  onConceptClick={handleConceptClick}
                />
              </div>
            </div>

            {/* Error display */}
            {error && <p className="mt-4 text-center text-red-500">{error}</p>}
          </div>
        )}
      </main>
    </div>
  );
}
