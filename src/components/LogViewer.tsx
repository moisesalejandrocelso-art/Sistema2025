import { useAutomationStore } from "@/lib/automation-store";
import { useRef, useEffect } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const levelColors: Record<string, string> = {
  info: "text-info",
  success: "text-success",
  warning: "text-warning",
  error: "text-destructive",
};

const levelBg: Record<string, string> = {
  info: "bg-info/10",
  success: "bg-success/10",
  warning: "bg-warning/10",
  error: "bg-destructive/10",
};

export function LogViewer() {
  const { logs, clearLogs } = useAutomationStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Consola</span>
        <Button variant="ghost" size="sm" onClick={clearLogs} className="h-6 px-2 text-muted-foreground hover:text-foreground">
          <Trash2 className="h-3 w-3 mr-1" /> Limpiar
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-0.5 font-mono text-[11px]">
        {logs.length === 0 && (
          <div className="text-muted-foreground text-center py-8">Sin logs. Ejecuta un flujo para ver la salida.</div>
        )}
        {logs.map((log) => (
          <div key={log.id} className={`flex items-start gap-2 px-2 py-1 rounded ${levelBg[log.level]}`}>
            <span className="text-muted-foreground shrink-0 w-16">
              {new Date(log.timestamp).toLocaleTimeString("es-MX", { hour12: false })}
            </span>
            <span className={`shrink-0 w-5 uppercase font-bold ${levelColors[log.level]}`}>
              {log.level === "info" ? "INF" : log.level === "success" ? "OK" : log.level === "warning" ? "WRN" : "ERR"}
            </span>
            <span className={`${levelColors[log.level]} break-all`}>{log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
