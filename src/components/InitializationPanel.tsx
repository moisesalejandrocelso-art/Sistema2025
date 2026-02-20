import { useConfigStore } from "@/lib/config-store";
import { useAutomationStore } from "@/lib/automation-store";
import { Button } from "@/components/ui/button";
import {
  Rocket, CheckCircle2, XCircle, Loader2, Circle, RefreshCw, Wifi, WifiOff,
} from "lucide-react";
import { useState } from "react";
import { runInitialization, checkHealth, connectWebSocket, type WsMessage } from "@/lib/api-client";

export function InitializationPanel() {
  const { config, initSteps, updateInitStep, setInitSteps, setIsInitialized, isInitialized } = useConfigStore();
  const { addLog } = useAutomationStore();
  const [backendStatus, setBackendStatus] = useState<"unknown" | "online" | "offline">("unknown");

  const resetSteps = () => {
    setInitSteps([
      { id: "check_appium", name: "Verificar servidor Appium", status: "pending" },
      { id: "open_app", name: "Abrir aplicación POS", status: "pending" },
      { id: "connect_appium", name: "Conectar sesión Appium", status: "pending" },
      { id: "clear_order", name: "Limpiar pedido anterior", status: "pending" },
      { id: "load_products", name: "Cargar lista de productos", status: "pending" },
    ]);
    setIsInitialized(false);
  };

  const testConnection = async () => {
    try {
      const res = await checkHealth();
      setBackendStatus("online");
      addLog("success", `Backend conectado (v${res.version}). Appium: ${res.appium_connected ? "✓" : "✗"}`);
    } catch {
      setBackendStatus("offline");
      addLog("error", "No se pudo conectar al backend. ¿Está corriendo python main.py en localhost:8000?");
    }
  };

  const runInit = async () => {
    resetSteps();
    addLog("info", "▶ Iniciando secuencia de inicialización (backend real)...");

    // Connect WebSocket for real-time updates
    const ws = connectWebSocket((msg: WsMessage) => {
      if (msg.type === "log") {
        addLog(msg.level as "info" | "success" | "warning" | "error", msg.message);
      }
      if (msg.type === "status" && msg.data) {
        const d = msg.data as { step_id?: string; status?: string; message?: string };
        if (d.step_id && d.status) {
          updateInitStep(d.step_id, {
            status: d.status as "pending" | "running" | "success" | "error",
            message: d.message,
          });
        }
      }
    });

    try {
      // Mark all steps as pending initially
      for (const step of initSteps) {
        updateInitStep(step.id, { status: "pending" });
      }

      const result = await runInitialization({
        app_path: config.appPath,
        appium_url: config.appiumUrl,
        products_file: config.productsFile,
        products: config.products,
        iterations: config.iterations,
        combo_box_name: config.comboBoxName,
        combo_box_option: config.comboBoxOption,
        radio_button_name: config.radioButtonName,
        payment_amount: config.paymentAmount,
        step_delay: config.stepDelay,
        retry_attempts: config.retryAttempts,
        retry_delay: config.retryDelay,
        enable_debug: config.enableDebug,
      });

      if (result.status === "success") {
        setIsInitialized(true);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      addLog("error", `Error de inicialización: ${message}`);
    } finally {
      setTimeout(() => ws.close(), 1000);
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case "pending": return <Circle className="h-4 w-4 text-muted-foreground" />;
      case "running": return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case "success": return <CheckCircle2 className="h-4 w-4 text-success" />;
      case "error": return <XCircle className="h-4 w-4 text-destructive" />;
      default: return <Circle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const isRunning = initSteps.some((s) => s.status === "running");

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Rocket className="h-5 w-5 text-primary" />
        <h2 className="font-mono text-sm font-bold text-foreground">Inicialización del Sistema</h2>
      </div>

      {/* Backend connection test */}
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={testConnection} className="font-mono text-[11px] gap-1.5">
          {backendStatus === "online" ? <Wifi className="h-3 w-3 text-success" /> : <WifiOff className="h-3 w-3 text-muted-foreground" />}
          Probar Conexión Backend
        </Button>
        <span className={`text-[10px] font-mono ${
          backendStatus === "online" ? "text-success" :
          backendStatus === "offline" ? "text-destructive" :
          "text-muted-foreground"
        }`}>
          {backendStatus === "online" ? "● Conectado" :
           backendStatus === "offline" ? "● Desconectado" :
           "● Sin verificar"}
        </span>
      </div>

      <p className="text-xs text-muted-foreground font-mono">
        Ejecuta la secuencia de inicio: abre la aplicación POS, conecta con Appium, limpia el pedido anterior y carga los productos.
      </p>

      {/* Config summary */}
      <div className="rounded-md border border-border bg-secondary/30 p-3 space-y-1 font-mono text-[11px]">
        <div className="flex justify-between">
          <span className="text-muted-foreground">App:</span>
          <span className="text-foreground truncate ml-4 max-w-[260px]">{config.appPath.split("\\").pop()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Appium:</span>
          <span className="text-foreground">{config.appiumUrl}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Productos:</span>
          <span className="text-primary">{config.products.length} cargados</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Iteraciones:</span>
          <span className="text-foreground">{config.iterations}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Debug:</span>
          <span className={config.enableDebug ? "text-warning" : "text-muted-foreground"}>
            {config.enableDebug ? "Activado" : "Desactivado"}
          </span>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {initSteps.map((step, i) => (
          <div
            key={step.id}
            className={`flex items-center gap-3 p-3 rounded-md border transition-all ${
              step.status === "running" ? "border-primary bg-primary/5 glow-primary" :
              step.status === "success" ? "border-success/30 bg-success/5" :
              step.status === "error" ? "border-destructive/30 bg-destructive/5" :
              "border-border bg-card"
            }`}
          >
            <span className="font-mono text-[10px] text-muted-foreground w-4">{i + 1}</span>
            {statusIcon(step.status)}
            <div className="flex-1">
              <span className="text-xs font-medium">{step.name}</span>
              {step.message && (
                <span className={`block text-[10px] font-mono mt-0.5 ${
                  step.status === "error" ? "text-destructive" : "text-muted-foreground"
                }`}>
                  {step.message}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 pt-2">
        <Button
          onClick={runInit}
          disabled={isRunning}
          className="flex-1 bg-primary text-primary-foreground hover:bg-primary/80 font-mono text-xs gap-2"
        >
          {isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Rocket className="h-3.5 w-3.5" />}
          {isRunning ? "Inicializando..." : "Iniciar Sistema"}
        </Button>
        <Button variant="outline" onClick={resetSteps} disabled={isRunning} className="font-mono text-xs gap-1">
          <RefreshCw className="h-3 w-3" /> Reset
        </Button>
      </div>

      {isInitialized && (
        <div className="rounded-md border border-success/30 bg-success/10 p-3 text-xs font-mono text-success flex items-center gap-2 animate-slide-in">
          <CheckCircle2 className="h-4 w-4" />
          Sistema inicializado. Puedes ir a la pestaña "Flujos" para ejecutar automatizaciones.
        </div>
      )}
    </div>
  );
}
