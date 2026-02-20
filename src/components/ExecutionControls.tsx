import { Play, Pause, Square, SkipForward } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAutomationStore } from "@/lib/automation-store";
import { useFlowRunner } from "@/lib/flow-runner";
import { RecordButton } from "@/components/RecordButton";

export function ExecutionControls() {
  const { executionStatus, isRecording, startFromStepIndex, setStartFromStepIndex, flows, activeFlowId } = useAutomationStore();
  const { runFlow, pauseFlow, stopFlow } = useFlowRunner();

  const isRunning = executionStatus === "running";
  const isPaused = executionStatus === "paused";
  const activeFlow = flows.find((f) => f.id === activeFlowId);
  const totalSteps = activeFlow?.steps.filter((s) => s.enabled).length || 0;

  const handleStop = () => {
    stopFlow();
  };

  return (
    <div className="flex items-center gap-2">
      {/* Record button */}
      <RecordButton />

      <div className="w-px h-5 bg-border" />

      {!isRunning && !isPaused ? (
        <Button
          size="sm"
          onClick={runFlow}
          disabled={isRecording}
          className="bg-success hover:bg-success/80 text-success-foreground glow-success gap-1.5 font-mono text-xs"
        >
          <Play className="h-3.5 w-3.5" />
          {startFromStepIndex > 0 ? `Desde paso ${startFromStepIndex + 1}` : "Ejecutar"}
        </Button>
      ) : (
        <Button
          size="sm"
          variant="outline"
          onClick={pauseFlow}
          className="border-warning text-warning hover:bg-warning/10 gap-1.5 font-mono text-xs"
        >
          <Pause className="h-3.5 w-3.5" />
          Pausar
        </Button>
      )}
      <Button
        size="sm"
        variant="outline"
        onClick={handleStop}
        disabled={!isRunning && !isPaused}
        className="border-destructive text-destructive hover:bg-destructive/10 gap-1.5 font-mono text-xs"
      >
        <Square className="h-3.5 w-3.5" />
        Detener
      </Button>
      {startFromStepIndex > 0 && !isRunning && !isPaused && (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setStartFromStepIndex(0)}
          className="gap-1 font-mono text-[10px] text-muted-foreground hover:text-foreground h-7 px-2"
        >
          <SkipForward className="h-3 w-3" />
          Reset inicio
        </Button>
      )}
      <div className="ml-2 flex items-center gap-1.5">
        <span
          className={`h-2 w-2 rounded-full ${
            isRecording ? "bg-destructive animate-pulse" :
            isRunning ? "bg-success animate-pulse-glow" :
            isPaused ? "bg-warning" :
            executionStatus === "error" ? "bg-destructive" :
            executionStatus === "completed" ? "bg-success" :
            "bg-muted-foreground"
          }`}
        />
        <span className="font-mono text-[11px] text-muted-foreground uppercase tracking-wider">
          {isRecording ? "Grabando..." :
           executionStatus === "idle" ? "Listo" :
           executionStatus === "running" ? "Ejecutando..." :
           executionStatus === "paused" ? "Pausado" :
           executionStatus === "stopped" ? "Detenido" :
           executionStatus === "completed" ? "Completado" :
           "Error"}
        </span>
      </div>
    </div>
  );
}
