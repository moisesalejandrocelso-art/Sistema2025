import { create } from "zustand";
import { persist } from "zustand/middleware";
import type {
  AutomationFlow,
  FlowStep,
  LogEntry,
  ElementSelector,
  ExecutionStatus,
  LogLevel,
} from "./automation-types";
import { generateId } from "./automation-types";

export interface StepFailureInfo {
  stepIndex: number;
  stepDescription: string;
  error: string;
  selectorType?: string;
  selectorValue?: string;
  actionType?: string;
}

interface AutomationState {
  flows: AutomationFlow[];
  activeFlowId: string | null;
  elementLibrary: ElementSelector[];
  logs: LogEntry[];
  executionStatus: ExecutionStatus;
  currentStepIndex: number;
  startFromStepIndex: number;
  stepFailure: StepFailureInfo | null;
  wsRef: WebSocket | null;
  isRecording: boolean;

  // Flow actions
  addFlow: (name: string, description: string) => void;
  deleteFlow: (id: string) => void;
  setActiveFlow: (id: string | null) => void;
  updateFlow: (id: string, updates: Partial<AutomationFlow>) => void;

  // Step actions
  addStep: (flowId: string, step: Omit<FlowStep, "id" | "order">) => void;
  updateStep: (flowId: string, stepId: string, updates: Partial<FlowStep>) => void;
  deleteStep: (flowId: string, stepId: string) => void;
  reorderSteps: (flowId: string, fromIndex: number, toIndex: number) => void;

  // Element library
  addElement: (element: Omit<ElementSelector, "id">) => void;
  deleteElement: (id: string) => void;

  // Execution
  setExecutionStatus: (status: ExecutionStatus) => void;
  setCurrentStepIndex: (index: number) => void;
  setStartFromStepIndex: (index: number) => void;
  setStepFailure: (failure: StepFailureInfo | null) => void;
  setWsRef: (ws: WebSocket | null) => void;
  setIsRecording: (v: boolean) => void;

  // Logs
  addLog: (level: LogLevel, message: string, stepId?: string) => void;
  clearLogs: () => void;
}

// Sample data
const sampleElements: ElementSelector[] = [
  { id: generateId(), label: "Botón Borrar Pedido", selectorType: "name", selectorValue: "Borrar pedido", description: "Botón para limpiar el pedido actual" },
  { id: generateId(), label: "Campo Búsqueda", selectorType: "xpath", selectorValue: "//*[@AutomationId='txtBusca']", description: "Campo de búsqueda de productos" },
  { id: generateId(), label: "ComboBox Venta asignada", selectorType: "name", selectorValue: "Venta asignada a", description: "ComboBox para asignar vendedor" },
  { id: generateId(), label: "Botón Continuar", selectorType: "name", selectorValue: "Continuar", description: "Botón para continuar con la venta" },
  { id: generateId(), label: "RadioButton Consumidor Final", selectorType: "name", selectorValue: "Consumidor final", description: "RadioButton tipo de cliente" },
  { id: generateId(), label: "Campo de Cobro", selectorType: "xpath", selectorValue: "//*[@AutomationId='InputBox']", description: "Campo para ingresar monto" },
  { id: generateId(), label: "Botón Aceptar", selectorType: "name", selectorValue: "Aceptar", description: "Botón de confirmación en modales" },
];

const sampleFlow: AutomationFlow = {
  id: generateId(),
  name: "Flujo de Venta Completa",
  description: "Limpiar pedido, buscar productos, seleccionar vendedor, continuar venta y procesar pago",
  steps: [
    { id: generateId(), order: 0, actionType: "click", description: "Borrar pedido anterior", enabled: true, elementSelector: sampleElements[0] },
    { id: generateId(), order: 1, actionType: "search_product", description: "Buscar productos desde lista", value: "{{products}}", enabled: true, elementSelector: sampleElements[1] },
    { id: generateId(), order: 2, actionType: "select_combo", description: "Seleccionar vendedor en ComboBox", enabled: true, elementSelector: sampleElements[2] },
    { id: generateId(), order: 3, actionType: "click", description: "Continuar con la venta (1)", enabled: true, elementSelector: sampleElements[3] },
    { id: generateId(), order: 4, actionType: "select_radio", description: "Seleccionar RadioButton Consumidor final", enabled: true, elementSelector: sampleElements[4] },
    { id: generateId(), order: 5, actionType: "click", description: "Continuar con la venta (2)", enabled: true, elementSelector: sampleElements[3] },
    { id: generateId(), order: 6, actionType: "type", description: "Ingresar monto de pago", value: "{{payment_amount}}", enabled: true, elementSelector: sampleElements[5] },
    { id: generateId(), order: 7, actionType: "send_keys", description: "Confirmar con Enter", value: "Enter", enabled: true },
  ],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

export const useAutomationStore = create<AutomationState>()(
  persist(
    (set) => ({
      flows: [sampleFlow],
      activeFlowId: sampleFlow.id,
      elementLibrary: sampleElements,
      logs: [],
      executionStatus: "idle",
      currentStepIndex: -1,
      startFromStepIndex: 0,
      stepFailure: null,
      wsRef: null,
      isRecording: false,

      addFlow: (name, description) => {
        const flow: AutomationFlow = {
          id: generateId(),
          name,
          description,
          steps: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        set((s) => ({ flows: [...s.flows, flow], activeFlowId: flow.id }));
      },

      deleteFlow: (id) =>
        set((s) => ({
          flows: s.flows.filter((f) => f.id !== id),
          activeFlowId: s.activeFlowId === id ? null : s.activeFlowId,
        })),

      setActiveFlow: (id) => set({ activeFlowId: id }),

      updateFlow: (id, updates) =>
        set((s) => ({
          flows: s.flows.map((f) => (f.id === id ? { ...f, ...updates, updatedAt: new Date().toISOString() } : f)),
        })),

      addStep: (flowId, step) =>
        set((s) => ({
          flows: s.flows.map((f) => {
            if (f.id !== flowId) return f;
            const newStep: FlowStep = { ...step, id: generateId(), order: f.steps.length };
            return { ...f, steps: [...f.steps, newStep], updatedAt: new Date().toISOString() };
          }),
        })),

      updateStep: (flowId, stepId, updates) =>
        set((s) => ({
          flows: s.flows.map((f) => {
            if (f.id !== flowId) return f;
            return { ...f, steps: f.steps.map((st) => (st.id === stepId ? { ...st, ...updates } : st)), updatedAt: new Date().toISOString() };
          }),
        })),

      deleteStep: (flowId, stepId) =>
        set((s) => ({
          flows: s.flows.map((f) => {
            if (f.id !== flowId) return f;
            const steps = f.steps.filter((st) => st.id !== stepId).map((st, i) => ({ ...st, order: i }));
            return { ...f, steps, updatedAt: new Date().toISOString() };
          }),
        })),

      reorderSteps: (flowId, fromIndex, toIndex) =>
        set((s) => ({
          flows: s.flows.map((f) => {
            if (f.id !== flowId) return f;
            const steps = [...f.steps];
            const [moved] = steps.splice(fromIndex, 1);
            steps.splice(toIndex, 0, moved);
            return { ...f, steps: steps.map((st, i) => ({ ...st, order: i })), updatedAt: new Date().toISOString() };
          }),
        })),

      addElement: (element) =>
        set((s) => ({ elementLibrary: [...s.elementLibrary, { ...element, id: generateId() }] })),

      deleteElement: (id) =>
        set((s) => ({ elementLibrary: s.elementLibrary.filter((e) => e.id !== id) })),

      setExecutionStatus: (status) => set({ executionStatus: status }),
      setCurrentStepIndex: (index) => set({ currentStepIndex: index }),
      setStartFromStepIndex: (index) => set({ startFromStepIndex: index }),
      setStepFailure: (failure) => set({ stepFailure: failure }),
      setWsRef: (ws) => set({ wsRef: ws }),
      setIsRecording: (v) => set({ isRecording: v }),

      addLog: (level, message, stepId) =>
        set((s) => ({
          logs: [...s.logs, { id: generateId(), timestamp: new Date().toISOString(), level, message, stepId }],
        })),

      clearLogs: () => set({ logs: [] }),
    }),
    {
      name: "automation-store",
      partialize: (state) => ({
        flows: state.flows,
        activeFlowId: state.activeFlowId,
        elementLibrary: state.elementLibrary,
      }),
    }
  )
);
