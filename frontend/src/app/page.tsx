"use client";

import { useState } from "react";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { MarkdownContent } from "@/components/MarkdownContent";
import { SlidePayload, startLecture, performAction } from "@/lib/api";

export default function Home() {
  const [topic, setTopic] = useState("");
  const [slide, setSlide] = useState<SlidePayload | null>(null);
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

  async function handleAction(action: string, params?: Record<string, unknown>) {
    if (!slide?.session_id) return;

    setActionLoading(true);
    setError(null);
    try {
      const result = await performAction(slide.session_id, action, params);
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
    // Trigger a deep dive when clicking on a concept in the mindmap
    handleAction("deep_dive", { concept });
  }

  // Get button style based on action type
  function getButtonStyle(action: string): string {
    const baseStyle =
      "h-9 rounded-lg px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 md:h-10 md:px-4 md:text-base";

    switch (action) {
      // Navigation - primary blue
      case "advance_main_thread":
      case "go_previous":
      case "extend_lecture":
        return `${baseStyle} bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700`;

      // Deep dive - purple/indigo
      case "deep_dive":
        return `${baseStyle} bg-indigo-100 text-indigo-800 border border-indigo-300 hover:bg-indigo-200 dark:bg-indigo-900/50 dark:text-indigo-200 dark:border-indigo-700 dark:hover:bg-indigo-800/50`;

      // Examples and Quiz - teal/green
      case "show_example":
      case "quiz_me":
      case "quiz_answer":
        return `${baseStyle} bg-teal-100 text-teal-800 border border-teal-300 hover:bg-teal-200 dark:bg-teal-900/50 dark:text-teal-200 dark:border-teal-700 dark:hover:bg-teal-800/50`;

      // Return/back actions - subtle gray
      case "return_to_main":
        return `${baseStyle} bg-zinc-200 text-zinc-700 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-600`;

      // References and concept map - amber/orange
      case "show_references":
      case "show_concept_map":
        return `${baseStyle} bg-amber-100 text-amber-800 border border-amber-300 hover:bg-amber-200 dark:bg-amber-900/50 dark:text-amber-200 dark:border-amber-700 dark:hover:bg-amber-800/50`;

      // Clarify (formerly simplify) - light purple
      case "clarify_slide":
        return `${baseStyle} bg-purple-100 text-purple-800 border border-purple-300 hover:bg-purple-200 dark:bg-purple-900/50 dark:text-purple-200 dark:border-purple-700 dark:hover:bg-purple-800/50`;

      // Regenerate - rose/pink with refresh connotation
      case "regenerate_slide":
        return `${baseStyle} bg-rose-100 text-rose-800 border border-rose-300 hover:bg-rose-200 dark:bg-rose-900/50 dark:text-rose-200 dark:border-rose-700 dark:hover:bg-rose-800/50`;

      // Default - neutral
      default:
        return `${baseStyle} border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700`;
    }
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
                  Slide {slide.slide_index + 1} of {slide.total_slides}
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
                    width: `${((slide.slide_index + 1) / slide.total_slides) * 100}%`,
                  }}
                />
              </div>
            </div>

            {/* Slide content - scrollable, takes remaining space */}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <div className="rounded-xl bg-white p-6 shadow-lg dark:bg-zinc-800 md:p-8">
                <h2 className="mb-4 text-xl font-bold text-zinc-900 dark:text-zinc-100 md:text-2xl">
                  {slide.content.title}
                </h2>
                <div className="text-base leading-relaxed text-zinc-700 dark:text-zinc-300 md:text-lg">
                  <MarkdownContent
                    content={slide.content.text}
                    onConceptClick={handleConceptClick}
                  />
                </div>
              </div>
            </div>

            {/* Interactive controls - fixed height at bottom */}
            <div className="flex-shrink-0 pt-4">
              {error && <p className="mb-3 text-center text-red-500">{error}</p>}
              <div className="flex min-h-[80px] flex-wrap content-start gap-2 md:gap-3">
                {slide.interactive_controls.map((control, index) => (
                  <button
                    key={index}
                    onClick={() => handleAction(control.action, control.params)}
                    disabled={actionLoading}
                    className={getButtonStyle(control.action)}
                  >
                    {actionLoading ? "..." : control.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
