import { useState } from "react";
import { pickElements, reconnectAppium, type CapturedElement } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Crosshair, Loader2, Search, Square, AlertCircle, RefreshCw } from "lucide-react";

interface ElementPickerProps {
  onSelect: (selectorType: string, selectorValue: string, description: string) => void;
}

export function ElementPicker({ onSelect }: ElementPickerProps) {
  const [elements, setElements] = useState<CapturedElement[]>([]);
  const [loading, setLoading] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [error, setError] = useState("");
  const [sessionExpired, setSessionExpired] = useState(false);
  const [filter, setFilter] = useState("");
  const [expanded, setExpanded] = useState(false);

  const handleReconnect = async () => {
    setReconnecting(true);
    setError("");
    try {
      const result = await reconnectAppium();
      if (result.status === "success") {
        setSessionExpired(false);
        setError("");
        // Auto-capture after reconnect
        await handleCapture();
      } else {
        setError(result.error || "No se pudo reconectar");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error reconectando");
    } finally {
      setReconnecting(false);
    }
  };

  const handleCapture = async () => {
    setLoading(true);
    setError("");
    setSessionExpired(false);
    try {
      const result = await pickElements();
      if (result.status === "success") {
        setElements(result.elements);
        setExpanded(true);
      } else {
        const res = result as any;
        if (res.error === "session_expired") {
          setSessionExpired(true);
          setError(res.message || "Sesión expirada");
        } else {
          setError(res.error || res.message || "Error capturando elementos");
        }
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error de conexión";
      if (msg.includes("terminated or not started") || msg.includes("session")) {
        setSessionExpired(true);
        setError("La sesión de Appium expiró.");
      } else {
        setError(msg.includes("fetch")
          ? "No se pudo conectar al backend. ¿Está corriendo python main.py?"
          : msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectElement = (el: CapturedElement) => {
    let selectorType = "name";
    let selectorValue = el.name;
    let description = el.name || el.text;

    if (el.automationId) {
      selectorType = "xpath";
      selectorValue = `//*[@AutomationId='${el.automationId}']`;
      description = el.automationId;
    } else if (el.name) {
      selectorType = "name";
      selectorValue = el.name;
    } else if (el.text) {
      selectorType = "name";
      selectorValue = el.text;
    }

    onSelect(selectorType, selectorValue, `${el.controlType}: ${description}`);
    setExpanded(false);
  };

  const filtered = elements.filter((el) => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return (
      (el.name && el.name.toLowerCase().includes(q)) ||
      (el.automationId && el.automationId.toLowerCase().includes(q)) ||
      (el.text && el.text.toLowerCase().includes(q)) ||
      (el.controlType && el.controlType.toLowerCase().includes(q))
    );
  });

  if (!expanded) {
    return (
      <div className="space-y-1">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCapture}
          disabled={loading || reconnecting}
          className="w-full gap-1.5 font-mono text-xs border-primary/40 text-primary hover:bg-primary/10"
        >
          {loading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Crosshair className="h-3 w-3" />
          )}
          {loading ? "Capturando elementos..." : "Seleccionar del POS"}
        </Button>
        {sessionExpired && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleReconnect}
            disabled={reconnecting}
            className="w-full gap-1.5 font-mono text-xs border-orange-500/40 text-orange-600 hover:bg-orange-500/10"
          >
            {reconnecting ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="h-3 w-3" />
            )}
            {reconnecting ? "Reconectando..." : "Reconectar sesión Appium"}
          </Button>
        )}
        {error && (
          <div className="flex items-start gap-1.5 rounded-md border border-destructive/30 bg-destructive/10 p-2">
            <AlertCircle className="h-3 w-3 text-destructive shrink-0 mt-0.5" />
            <p className="text-[10px] font-mono text-destructive">{error}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-md border border-primary/30 bg-primary/5 p-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-primary font-semibold flex items-center gap-1.5">
          <Crosshair className="h-3.5 w-3.5" />
          Elementos del POS ({elements.length})
        </span>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={handleCapture} disabled={loading} className="h-6 px-2 text-[10px] font-mono">
            {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : "Refrescar"}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setExpanded(false)} className="h-6 px-2 text-[10px] font-mono">
            Cerrar
          </Button>
        </div>
      </div>

      {error && (
        <p className="text-[10px] font-mono text-destructive">{error}</p>
      )}

      <div className="relative">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filtrar elementos..."
          className="h-7 text-[11px] font-mono pl-7"
        />
      </div>

      <ScrollArea className="h-[200px]">
        <div className="space-y-1">
          {filtered.map((el, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectElement(el)}
              className="w-full text-left rounded px-2 py-1.5 hover:bg-primary/10 transition-colors border border-transparent hover:border-primary/30 group"
            >
              <div className="flex items-center gap-2">
                <Square className="h-3 w-3 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono px-1 rounded bg-secondary text-muted-foreground">
                      {el.controlType}
                    </span>
                    <span className="text-[11px] font-mono text-foreground truncate">
                      {el.name || el.text || el.automationId || "(sin nombre)"}
                    </span>
                  </div>
                  <div className="flex gap-2 mt-0.5">
                    {el.automationId && (
                      <span className="text-[9px] font-mono text-muted-foreground/70">
                        ID: {el.automationId}
                      </span>
                    )}
                    {el.className && (
                      <span className="text-[9px] font-mono text-muted-foreground/70">
                        Class: {el.className}
                      </span>
                    )}
                    <span className="text-[9px] font-mono text-muted-foreground/70">
                      [{el.x},{el.y}] {el.width}x{el.height}
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="text-[10px] font-mono text-muted-foreground text-center py-4">
              {elements.length === 0 ? "Sin elementos. ¿Está el POS abierto?" : "Sin resultados para el filtro."}
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}