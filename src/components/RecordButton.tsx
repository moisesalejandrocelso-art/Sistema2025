import { useState } from "react";
import { Circle, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAutomationStore } from "@/lib/automation-store";
import {
  startRecording,
  stopRecording,
  connectWebSocket,
  type WsMessage,
} from "@/lib/api-client";
import type { ActionType, SelectorType } from "@/lib/automation-types";
import { generateId } from "@/lib/automation-types";

export function RecordButton() {
  const {
    isRecording,
    setIsRecording,
    activeFlowId,
    flows,
    addLog,
    addStep,
    setWsRef,
  } = useAutomationStore();
  const [recordWs, setRecordWs] = useState<WebSocket | null>(null);
  const [addedStepCount, setAddedStepCount] = useState(0);

  const handleStartRecording = async () => {
    if (!activeFlowId) {
      addLog("warning", "Selecciona o crea un flujo antes de grabar.");
      return;
    }

    setAddedStepCount(0);

    try {
      // Close any previous WS
      const prevWs = useAutomationStore.getState().wsRef;
      if (prevWs && prevWs.readyState === WebSocket.OPEN) {
        prevWs.close();
      }

      // Connect WebSocket for receiving recorded steps in real-time
      const ws = connectWebSocket((msg: WsMessage) => {
        if (msg.type === "log") {
          addLog(msg.level as "info" | "success" | "warning" | "error", msg.message);
        }
        if (msg.type === "status") {
          const wsMsg = msg as any;
          if (wsMsg.status === "recorded_step" && wsMsg.data) {
            const stepData = wsMsg.data as Record<string, unknown>;
            const flowId = useAutomationStore.getState().activeFlowId;
            if (!flowId) return;

            const actionType = (stepData.action_type as ActionType) || "click";
            const selectorType = stepData.selector_type as SelectorType | undefined;
            const selectorValue = stepData.selector_value as string | undefined;

            addStep(flowId, {
              actionType,
              description: (stepData.description as string) || `${actionType} grabado`,
              enabled: true,
              value: stepData.value as string | undefined,
              waitTime: stepData.wait_time as number | undefined,
              elementSelector: selectorType && selectorValue
                ? {
                    id: generateId(),
                    label: selectorValue,
                    selectorType,
                    selectorValue,
                    description: "Capturado automáticamente",
                  }
                : undefined,
            });

            setAddedStepCount((c) => c + 1);
            addLog("info", `🔴 Paso grabado: ${stepData.description || actionType}`);
          }
        }
      });

      setRecordWs(ws);
      setWsRef(ws);

      await startRecording();
      setIsRecording(true);
      addLog("success", "🔴 Grabación iniciada. Interactúa con el POS...");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      addLog("error", `Error al iniciar grabación: ${message}`);
    }
  };

  const handleStopRecording = async () => {
    try {
      const result = await stopRecording();
      setIsRecording(false);

      const flowId = useAutomationStore.getState().activeFlowId;
      const flow = flowId ? useAutomationStore.getState().flows.find((f) => f.id === flowId) : null;

      // Fallback: if backend returned steps that weren't added via WS, add them now
      if (result.steps && result.steps.length > 0 && flowId && flow) {
        const existingCount = flow.steps.length;
        const wsAdded = addedStepCount;
        const backendTotal = result.steps.length;

        if (wsAdded < backendTotal) {
          // Add missing steps (the ones not received via WebSocket)
          const missingSteps = result.steps.slice(wsAdded);
          for (const stepData of missingSteps) {
            const actionType = (stepData.action_type as ActionType) || "click";
            const selectorType = stepData.selector_type as SelectorType | undefined;
            const selectorValue = stepData.selector_value as string | undefined;

            addStep(flowId, {
              actionType,
              description: (stepData.description as string) || `${actionType} grabado`,
              enabled: true,
              value: stepData.value as string | undefined,
              waitTime: stepData.wait_time as number | undefined,
              elementSelector: selectorType && selectorValue
                ? {
                    id: generateId(),
                    label: selectorValue,
                    selectorType,
                    selectorValue,
                    description: "Capturado automáticamente",
                  }
                : undefined,
            });
          }
          addLog("info", `📋 ${missingSteps.length} pasos adicionales sincronizados desde backend`);
        }
      }

      addLog("success", `⏹ Grabación detenida. ${result.count} pasos capturados y agregados al flujo.`);

      if (recordWs) {
        recordWs.close();
        setRecordWs(null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      addLog("error", `Error al detener grabación: ${message}`);
      setIsRecording(false);
    }
  };

  return isRecording ? (
    <Button
      size="sm"
      onClick={handleStopRecording}
      className="bg-destructive hover:bg-destructive/80 text-destructive-foreground gap-1.5 font-mono text-xs animate-pulse"
    >
      <Square className="h-3 w-3" />
      Detener Grabación
    </Button>
  ) : (
    <Button
      size="sm"
      variant="outline"
      onClick={handleStartRecording}
      className="border-destructive/50 text-destructive hover:bg-destructive/10 gap-1.5 font-mono text-xs"
    >
      <Circle className="h-3 w-3 fill-destructive text-destructive" />
      Grabar Flujo
    </Button>
  );
}
