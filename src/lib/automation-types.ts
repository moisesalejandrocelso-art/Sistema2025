export type ActionType = "click" | "double_click" | "type" | "send_keys" | "wait" | "clear" | "select_combo" | "select_radio" | "scroll" | "assert" | "search_product";
export type SelectorType = "name" | "xpath" | "id" | "accessibility_id" | "css" | "class_name";
export type LogLevel = "info" | "success" | "warning" | "error";

export interface ElementSelector {
  id: string;
  label: string;
  selectorType: SelectorType;
  selectorValue: string;
  description?: string;
}

export interface FlowStep {
  id: string;
  order: number;
  actionType: ActionType;
  elementSelector?: ElementSelector;
  value?: string;
  waitTime?: number;
  description: string;
  enabled: boolean;
}

export interface AutomationFlow {
  id: string;
  name: string;
  description: string;
  steps: FlowStep[];
  createdAt: string;
  updatedAt: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  stepId?: string;
}

export type ExecutionStatus = "idle" | "running" | "paused" | "stopped" | "completed" | "error";

export const ACTION_LABELS: Record<ActionType, string> = {
  click: "Clic",
  double_click: "Doble Clic",
  type: "Escribir Texto",
  send_keys: "Enviar Teclas",
  wait: "Esperar",
  clear: "Limpiar Campo",
  select_combo: "Seleccionar ComboBox",
  select_radio: "Seleccionar RadioButton",
  scroll: "Scroll",
  assert: "Verificar Elemento",
  search_product: "Buscar Productos (lista)",
};

export const SELECTOR_LABELS: Record<SelectorType, string> = {
  name: "Name",
  xpath: "XPath",
  id: "ID",
  accessibility_id: "Accessibility ID",
  css: "CSS Selector",
  class_name: "Class Name",
};

let idCounter = 0;
export const generateId = () => `id_${Date.now()}_${++idCounter}`;
