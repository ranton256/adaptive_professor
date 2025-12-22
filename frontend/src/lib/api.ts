const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface HealthResponse {
  status: string;
  service: string;
}

export interface SlideContent {
  title: string;
  text: string;
  diagram_code?: string;
}

export interface InteractiveControl {
  label: string;
  action: string;
  params?: Record<string, unknown>;
}

export interface SlidePayload {
  type: string;
  slide_id: string;
  session_id: string | null;
  layout: string;
  content: SlideContent;
  interactive_controls: InteractiveControl[];
  allow_freeform_input: boolean;
  slide_index: number;
  total_slides: number;
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return response.json();
}

export async function startLecture(topic: string): Promise<SlidePayload> {
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
): Promise<SlidePayload> {
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
