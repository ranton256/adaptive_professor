"use client";

import { useState } from "react";
import { ConnectionStatus } from "@/components/ConnectionStatus";
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

  async function handleAction(action: string) {
    if (!slide?.session_id) return;

    setActionLoading(true);
    setError(null);
    try {
      const result = await performAction(slide.session_id, action);
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
          <div className="w-full max-w-2xl space-y-6">
            {/* Progress indicator */}
            <div className="flex items-center justify-between text-sm text-zinc-500 dark:text-zinc-400">
              <span>
                Slide {slide.slide_index + 1} of {slide.total_slides}
              </span>
              <div className="h-2 flex-1 mx-4 rounded-full bg-zinc-200 dark:bg-zinc-700">
                <div
                  className="h-2 rounded-full bg-blue-600 transition-all duration-300"
                  style={{
                    width: `${((slide.slide_index + 1) / slide.total_slides) * 100}%`,
                  }}
                />
              </div>
            </div>

            {/* Slide content */}
            <div className="rounded-xl bg-white p-8 shadow-lg dark:bg-zinc-800">
              <h2 className="mb-4 text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                {slide.content.title}
              </h2>
              <p className="text-lg leading-relaxed text-zinc-700 dark:text-zinc-300">
                {slide.content.text}
              </p>
            </div>

            {/* Interactive controls */}
            <div className="flex flex-wrap gap-3">
              {slide.interactive_controls.map((control, index) => (
                <button
                  key={index}
                  onClick={() => handleAction(control.action)}
                  disabled={actionLoading}
                  className="rounded-lg border border-zinc-300 bg-white px-4 py-2 font-medium text-zinc-900 transition-colors hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-100 dark:hover:bg-zinc-700"
                >
                  {actionLoading ? "..." : control.label}
                </button>
              ))}
            </div>

            {error && <p className="text-center text-red-500">{error}</p>}

            <button
              onClick={handleReset}
              className="text-sm text-zinc-500 underline hover:text-zinc-700 dark:hover:text-zinc-300"
            >
              Start new lecture
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
