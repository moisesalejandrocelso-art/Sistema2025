/**
 * API Client — Communicates with the local Python FastAPI backend.
 */
import { useConfigStore } from "./config-store";

function getApiBase(): string {
  return useConfigStore.getState().config.backendUrl.replace(/\/+$/, "");
}

function getWsBase(): string {
  const base = getApiBase();
  return base.replace(/^http/, "ws");
}

interface ApiResponse<T = unknown> {
  status: string;
  error?: string;
  [key: string]: unknown;
}

async function request<T = ApiResponse>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${getApiBase()}${endpoint}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ── Health ──────────────────────────────────────────────

export async function checkHealth() {
  return request<{ status: string; appium_connected: boolean; version: string }>("/api/health");
}

// ── Initialization ─────────────────────────────────────

export interface InitConfig {
  app_path: string;
  appium_url: string;
  products_file: string;
  products: { code: string; quantity: number }[];
  iterations: number;
  combo_box_name: string;
  combo_box_option: string;
  radio_button_name: string;
  payment_amount: number;
  step_delay: number;
  retry_attempts: number;
  retry_delay: number;
  enable_debug: boolean;
}

export async function runInitialization(config: InitConfig) {
  return request("/api/initialize", {
    method: "POST",
    body: JSON.stringify(config),
  });
}

// ── Flow Execution ─────────────────────────────────────

export interface FlowStepPayload {
  action_type: string;
  description: string;
  selector_type?: string;
  selector_value?: string;
  value?: string;
  wait_time?: number;
  enabled: boolean;
}

export interface RunFlowPayload {
  name: string;
  description: string;
  steps: FlowStepPayload[];
  iterations: number;
  config: InitConfig;
}

export async function runFlow(payload: RunFlowPayload) {
  return request("/api/run-flow", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function stopFlow() {
  return request("/api/stop-flow", { method: "POST" });
}

export async function pauseFlow() {
  return request("/api/pause-flow", { method: "POST" });
}

export async function resumeFlow() {
  return request("/api/resume-flow", { method: "POST" });
}

// ── Recording ─────────────────────────────────────────

export async function startRecording() {
  return request<{ status: string }>("/api/record/start", { method: "POST" });
}

export async function stopRecording() {
  return request<{ status: string; steps: FlowStepPayload[]; count: number }>(
    "/api/record/stop",
    { method: "POST" }
  );
}

export async function getRecordStatus() {
  return request<{ recording: boolean; steps_count: number; steps: FlowStepPayload[] }>(
    "/api/record/status"
  );
}

// ── Products File ─────────────────────────────────────

export async function loadProductsFromFile(filePath: string) {
  return request<{ status: string; products: { code: string; quantity: number }[]; count: number; error?: string }>(
    "/api/load-products-file",
    { method: "POST", body: JSON.stringify({ file_path: filePath }) }
  );
}

// ── Debug ──────────────────────────────────────────────

export interface CapturedElement {
  name: string;
  automationId: string;
  className: string;
  controlType: string;
  text: string;
  visible: boolean;
  enabled: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
}

export async function captureElements() {
  return request<{ status: string; elements: CapturedElement[] }>(
    "/api/debug/capture-elements",
    { method: "POST" }
  );
}

export async function pickElements() {
  return request<{ status: string; elements: CapturedElement[]; count: number }>(
    "/api/debug/pick-elements",
    { method: "POST" }
  );
}

export async function analyzeWindow() {
  return request<{ status: string; window_info: Record<string, unknown> }>(
    "/api/debug/analyze-window",
    { method: "POST" }
  );
}

export async function disconnectAppium() {
  return request("/api/disconnect", { method: "POST" });
}

export async function reconnectAppium(appiumUrl?: string) {
  return request<{ status: string; handle?: string; error?: string }>(
    "/api/reconnect",
    { method: "POST", body: JSON.stringify({ appium_url: appiumUrl || "http://127.0.0.1:4723" }) }
  );
}

// ── WebSocket ──────────────────────────────────────────

export type WsMessage =
  | { type: "log"; level: string; message: string }
  | { type: "status"; status: string; data?: Record<string, unknown> };

export function connectWebSocket(
  onMessage: (msg: WsMessage) => void,
  onClose?: () => void
): WebSocket {
  const ws = new WebSocket(`${getWsBase()}/ws`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as WsMessage;
      onMessage(data);
    } catch {
      // ignore malformed messages
    }
  };

  ws.onclose = () => onClose?.();

  return ws;
}
