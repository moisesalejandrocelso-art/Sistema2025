import { useAutomationStore } from "./automation-store";
import { useConfigStore } from "./config-store";
import {
  runFlow as apiRunFlow,
  stopFlow as apiStopFlow,
  pauseFlow as apiPauseFlow,
  connectWebSocket,
  type WsMessage,
} from "./api-client";

export function useFlowRunner() {
  const { flows, activeFlowId, setExecutionStatus, setCurrentStepIndex, addLog, clearLogs, setStepFailure, setWsRef, startFromStepIndex, setStartFromStepIndex } =
    useAutomationStore();
  const { config } = useConfigStore();

  const activeFlow = flows.find((f) => f.id === activeFlowId);

  const runFlow = async () => {
    if (!activeFlow || activeFlow.steps.length === 0) {
      addLog("warning", "No hay pasos para ejecutar.");
      return;
    }

    // Close any previous WebSocket to avoid duplicate messages
    const prevWs = useAutomationStore.getState().wsRef;
    if (prevWs && prevWs.readyState === WebSocket.OPEN) {
      prevWs.close();
    }
    setWsRef(null);

    clearLogs();
    setStepFailure(null);
    setExecutionStatus("running");
    addLog("info", `▶ Iniciando flujo: "${activeFlow.name}" (backend real)`);

    const ws = connectWebSocket((msg: WsMessage) => {
      if (msg.type === "log") {
        addLog(msg.level as "info" | "success" | "warning" | "error", msg.message);
      }
      if (msg.type === "status") {
        const wsMsg = msg as any;
        const statusValue = wsMsg.status as string | undefined;
        const d = (wsMsg.data || {}) as Record<string, unknown>;

        if (statusValue === "step_failed") {
          // Step failed — show retry dialog
          setStepFailure({
            stepIndex: d.step_index as number,
            stepDescription: d.step_description as string,
            error: d.error as string,
            selectorType: d.selector_type as string | undefined,
            selectorValue: d.selector_value as string | undefined,
            actionType: d.action_type as string | undefined,
          });
          setExecutionStatus("error");
          return;
        }

        // Normal status from data.status
        const execStatus = (d.status as string) || statusValue;
        if (execStatus && execStatus !== "step_failed") {
          setExecutionStatus(execStatus as "running" | "paused" | "stopped" | "completed" | "error");
        }
        if (typeof d.step_index === "number") {
          setCurrentStepIndex(d.step_index as number);
        }
      }
    });

    setWsRef(ws);

    try {
      const enabledSteps = activeFlow.steps.filter((s) => s.enabled);
      const startFrom = startFromStepIndex;
      
      if (startFrom > 0) {
        addLog("info", `⏩ Iniciando desde el paso ${startFrom + 1} de ${enabledSteps.length}`);
      }
      addLog("info", `📋 ${enabledSteps.length} pasos habilitados de ${activeFlow.steps.length} totales`);

      const payload = {
        name: activeFlow.name,
        description: activeFlow.description,
        steps: enabledSteps.map((s) => ({
          action_type: s.actionType,
          description: s.description,
          selector_type: s.elementSelector?.selectorType,
          selector_value: s.elementSelector?.selectorValue,
          value: s.value,
          wait_time: s.waitTime,
          enabled: s.enabled,
        })),
        iterations: config.iterations,
        start_from_step: startFrom,
        config: {
          app_path: config.appPath,
          appium_url: config.appiumUrl,
          products_file: config.productsFile,
          products: config.products,
          iterations: config.iterations,
          products_per_iteration: config.productsPerIteration,
          combo_box_name: config.comboBoxName,
          combo_box_option: config.comboBoxOption,
          radio_button_name: config.radioButtonName,
          payment_amount: config.paymentAmount,
          step_delay: config.stepDelay,
          retry_attempts: config.retryAttempts,
          retry_delay: config.retryDelay,
          enable_debug: config.enableDebug,
        },
      };

      const result = await apiRunFlow(payload);

      if (result.status === "error") {
        addLog("error", `Error: ${(result as any).error || "Error desconocido"}`);
        setExecutionStatus("error");
      } else if (result.status === "completed") {
        setExecutionStatus("completed");
        setCurrentStepIndex(-1);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      addLog("error", `Error ejecutando flujo: ${message}`);
      setExecutionStatus("error");
    }
  };

  const pauseFlow = async () => {
    try {
      await apiPauseFlow();
    } catch {
      setExecutionStatus("paused");
      addLog("warning", "⏸ Flujo pausado (local).");
    }
  };

  const stopFlow = async () => {
    try {
      await apiStopFlow();
    } catch {
      setExecutionStatus("stopped");
      setCurrentStepIndex(-1);
      addLog("warning", "⏹ Flujo detenido (local).");
    }
  };

  const sendStepResponse = (action: "retry" | "skip" | "stop", selectorType?: string, selectorValue?: string) => {
    const ws = useAutomationStore.getState().wsRef;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "step_response",
        action,
        selector_type: selectorType,
        selector_value: selectorValue,
      }));
    }
    setStepFailure(null);
    if (action === "stop") {
      setExecutionStatus("stopped");
      setCurrentStepIndex(-1);
    } else {
      setExecutionStatus("running");
    }
  };

  return { runFlow, pauseFlow, stopFlow, sendStepResponse };
}
