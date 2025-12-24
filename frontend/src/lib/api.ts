const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

import { A2UIMessage } from "./a2ui-types";

export interface HealthResponse {
  status: string;
  service: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function startLecture(topic: string): Promise<A2UIMessage> {
  const response = await fetch(`${API_BASE_URL}/api/lecture/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ topic }),
  });
  if (!response.ok) {
    throw new Error(`Failed to start lecture: ${response.status}`);
  }
  return response.json();
}

export async function performAction(
  sessionId: string,
  action: string,
  params?: Record<string, unknown>
): Promise<A2UIMessage> {
  const response = await fetch(`${API_BASE_URL}/api/lecture/${sessionId}/action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action, params }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Action failed: ${response.status}`);
  }
  return response.json();
}
