"use client";

import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

export type ConnectionState = "checking" | "connected" | "disconnected";

export function ConnectionStatus() {
  const [status, setStatus] = useState<ConnectionState>("checking");

  useEffect(() => {
    async function check() {
      try {
        const health = await checkHealth();
        if (health.status === "healthy") {
          setStatus("connected");
        } else {
          setStatus("disconnected");
        }
      } catch {
        setStatus("disconnected");
      }
    }
    check();
  }, []);

  return (
    <div data-testid="connection-status" className="flex items-center gap-2">
      <div
        className={`h-3 w-3 rounded-full ${
          status === "connected"
            ? "bg-green-500"
            : status === "disconnected"
              ? "bg-red-500"
              : "bg-yellow-500"
        }`}
      />
      <span className="text-sm">
        {status === "connected" && "Connected"}
        {status === "disconnected" && "Disconnected"}
        {status === "checking" && "Checking..."}
      </span>
    </div>
  );
}
