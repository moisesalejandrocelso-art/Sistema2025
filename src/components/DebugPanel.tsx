import { useConfigStore } from "@/lib/config-store";
import { useAutomationStore } from "@/lib/automation-store";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Bug, Eye, Camera, Trash2, Download, Loader2 } from "lucide-react";
import { useState } from "react";
import { captureElements as apiCaptureElements, type CapturedElement } from "@/lib/api-client";

export function DebugPanel() {
  const { config, updateConfig } = useConfigStore();
  const { addLog } = useAutomationStore();
  const [capturedElements, setCapturedElements] = useState<CapturedElement[]>([]);
  const [isCapturing, setIsCapturing] = useState(false);

  const handleCapture = async () => {
    setIsCapturing(true);
    addLog("info", "[DEBUG] Capturando elementos de pantalla (backend real)...");

    try {
      const res = await apiCaptureElements();
      if (res.status === "success") {
        setCapturedElements(res.elements);
        addLog("success", `[DEBUG] ${res.elements.length} elementos capturados`);
      } else {
        addLog("error", `[DEBUG] Error: ${res.status}`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error de conexión";
      addLog("error", `[DEBUG] ${message}. ¿Está corriendo el backend?`);
    } finally {
      setIsCapturing(false);
    }
  };

  const exportElements = () => {
    const text = capturedElements
      .map((el, i) => `${i + 1}. [${el.controlType}] Name="${el.name}" AutomationId="${el.automationId}" Text="${el.text}" Visible=${el.visible} Pos=(${el.x},${el.y}) Size=${el.width}x${el.height}`)
      .join("\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `screen_elements_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Bug className="h-5 w-5 text-warning" />
        <h2 className="font-mono text-sm font-bold text-foreground">Herramientas de Debug</h2>
      </div>

      <div className="flex items-center justify-between p-3 rounded-md border border-border bg-card">
        <div>
          <span className="text-xs font-medium">Modo Debug Global</span>
          <p className="text-[10px] font-mono text-muted-foreground mt-0.5">
            Captura elementos y análisis durante ejecución
          </p>
        </div>
        <Switch checked={config.enableDebug} onCheckedChange={(v) => updateConfig({ enableDebug: v })} />
      </div>

      <div className="space-y-2">
        <h3 className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Captura de Pantalla</h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCapture}
            disabled={isCapturing}
            className="font-mono text-xs gap-1.5 flex-1"
          >
            {isCapturing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Camera className="h-3.5 w-3.5" />}
            {isCapturing ? "Capturando..." : "Capturar Elementos"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportElements}
            disabled={capturedElements.length === 0}
            className="font-mono text-xs gap-1.5"
          >
            <Download className="h-3.5 w-3.5" /> Exportar
          </Button>
        </div>
      </div>

      {capturedElements.length > 0 && (
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs text-muted-foreground">
              {capturedElements.length} elementos encontrados
            </span>
            <button onClick={() => setCapturedElements([])} className="text-muted-foreground hover:text-foreground">
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
          {capturedElements.map((el, i) => (
            <div
              key={i}
              className={`flex items-center gap-2 px-2 py-1.5 rounded border text-xs font-mono transition ${
                el.visible ? "border-border bg-card" : "border-border/50 bg-muted/20 opacity-60"
              }`}
            >
              <Eye className={`h-3 w-3 shrink-0 ${el.visible ? "text-success" : "text-muted-foreground"}`} />
              <span className="text-[10px] px-1 py-0.5 rounded bg-secondary text-secondary-foreground shrink-0">
                {el.controlType}
              </span>
              <span className="text-foreground truncate flex-1">{el.name}</span>
              {el.automationId && (
                <span className="text-muted-foreground text-[10px] truncate max-w-20">#{el.automationId}</span>
              )}
              {el.text && el.text !== el.name && (
                <span className="text-muted-foreground text-[10px] truncate max-w-24">"{el.text}"</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
