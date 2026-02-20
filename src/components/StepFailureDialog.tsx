import { useState } from "react";
import { useAutomationStore } from "@/lib/automation-store";
import { useFlowRunner } from "@/lib/flow-runner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AlertTriangle, RotateCcw, SkipForward, Square, Pencil, Check, X } from "lucide-react";
import { ElementPicker } from "./ElementPicker";
import type { SelectorType } from "@/lib/automation-types";
import { generateId } from "@/lib/automation-types";

type EditState = "none" | "editing" | "confirming";

export function StepFailureDialog() {
  const { stepFailure, activeFlowId, flows, updateStep, setStartFromStepIndex } = useAutomationStore();
  const { sendStepResponse } = useFlowRunner();
  const [editState, setEditState] = useState<EditState>("none");
  const [selectorType, setSelectorType] = useState("");
  const [selectorValue, setSelectorValue] = useState("");
  const [pickerDescription, setPickerDescription] = useState("");

  if (!stepFailure) return null;


  const activeFlow = flows.find((f) => f.id === activeFlowId);
  const failedStep = activeFlow?.steps[stepFailure.stepIndex];

  const handleRetry = () => {
    if (editState === "confirming") {
      // Update the step in the flow before retrying
      if (activeFlowId && failedStep) {
        updateStep(activeFlowId, failedStep.id, {
          elementSelector: {
            id: failedStep.elementSelector?.id || generateId(),
            label: pickerDescription || failedStep.elementSelector?.label || "",
            selectorType: selectorType as SelectorType,
            selectorValue,
            description: pickerDescription || failedStep.elementSelector?.description || "",
          },
        });
      }
      sendStepResponse("retry", selectorType, selectorValue);
    } else {
      sendStepResponse("retry");
    }
    resetState();
  };

  const handleSkip = () => {
    sendStepResponse("skip");
    resetState();
  };

  const handleStop = () => {
    // Set startFromStepIndex to the failed step so user can resume from there
    if (stepFailure) {
      setStartFromStepIndex(stepFailure.stepIndex);
    }
    sendStepResponse("stop");
    resetState();
  };

  const resetState = () => {
    setEditState("none");
    setSelectorType("");
    setSelectorValue("");
    setPickerDescription("");
  };

  const handleEdit = () => {
    setSelectorType(stepFailure.selectorType || "name");
    setSelectorValue(stepFailure.selectorValue || "");
    setPickerDescription("");
    setEditState("editing");
  };

  const handlePickElement = (pickedSelectorType: string, pickedSelectorValue: string, description: string) => {
    setSelectorType(pickedSelectorType);
    setSelectorValue(pickedSelectorValue);
    setPickerDescription(description);
    setEditState("confirming");
  };

  const handleConfirmEdit = () => {
    setEditState("confirming");
  };

  const handleCancelEdit = () => {
    resetState();
  };

  return (
    <Dialog open={!!stepFailure} onOpenChange={(open) => { if (!open) handleStop(); }}>
      <DialogContent className="sm:max-w-[560px] border-destructive/50 bg-card max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive font-mono">
            <AlertTriangle className="h-5 w-5" />
            Error en Paso {stepFailure.stepIndex + 1}
          </DialogTitle>
          <DialogDescription className="font-mono text-xs">
            {stepFailure.stepDescription}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3">
            <p className="text-xs font-mono text-destructive">{stepFailure.error}</p>
          </div>

          <div className="rounded-md border border-border bg-secondary/30 p-3 space-y-1 font-mono text-[11px]">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Acción:</span>
              <span className="text-foreground">{stepFailure.actionType}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Selector actual:</span>
              <span className="text-foreground">[{stepFailure.selectorType}] {stepFailure.selectorValue}</span>
            </div>
            {editState !== "none" && (
              <div className="flex justify-between border-t border-border pt-1 mt-1">
                <span className="text-primary font-semibold">Nuevo selector:</span>
                <span className="text-primary font-semibold">[{selectorType}] {selectorValue}</span>
              </div>
            )}
          </div>

          {/* Confirmation state */}
          {editState === "confirming" && (
            <div className="rounded-md border border-primary/40 bg-primary/10 p-3 space-y-2">
              <p className="text-xs font-mono text-primary font-semibold">¿Confirmar nuevo selector?</p>
              <div className="font-mono text-[11px] space-y-1">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tipo:</span>
                  <span className="text-foreground">{selectorType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Valor:</span>
                  <span className="text-foreground break-all">{selectorValue}</span>
                </div>
                {pickerDescription && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Descripción:</span>
                    <span className="text-foreground">{pickerDescription}</span>
                  </div>
                )}
              </div>
              <div className="flex gap-2 pt-1">
                <Button size="sm" onClick={handleRetry} className="font-mono text-xs gap-1.5 flex-1">
                  <Check className="h-3 w-3" />
                  Confirmar y Reintentar
                </Button>
                <Button variant="outline" size="sm" onClick={handleCancelEdit} className="font-mono text-xs gap-1.5">
                  <X className="h-3 w-3" />
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          {/* Element Picker - visible when not confirming */}
          {editState !== "confirming" && (
            <ElementPicker onSelect={handlePickElement} />
          )}

          {/* Manual edit */}
          {editState === "editing" && (
            <div className="space-y-3 rounded-md border border-primary/30 bg-primary/5 p-3">
              <p className="text-xs font-mono text-primary font-semibold">Editar selector manualmente:</p>
              <div className="space-y-2">
                <Label className="text-xs font-mono">Tipo de selector</Label>
                <Select value={selectorType} onValueChange={setSelectorType}>
                  <SelectTrigger className="h-8 font-mono text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="name">Name</SelectItem>
                    <SelectItem value="xpath">XPath</SelectItem>
                    <SelectItem value="id">ID</SelectItem>
                    <SelectItem value="accessibility_id">Accessibility ID</SelectItem>
                    <SelectItem value="class_name">Class Name</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-mono">Valor del selector</Label>
                <Input
                  className="h-8 font-mono text-xs"
                  value={selectorValue}
                  onChange={(e) => setSelectorValue(e.target.value)}
                  placeholder="Ej: Borrar pedido"
                />
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleConfirmEdit} disabled={!selectorValue} className="font-mono text-xs gap-1.5 flex-1">
                  <Check className="h-3 w-3" />
                  Confirmar Cambio
                </Button>
                <Button variant="outline" size="sm" onClick={handleCancelEdit} className="font-mono text-xs gap-1.5">
                  <X className="h-3 w-3" />
                  Cancelar
                </Button>
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          {editState === "none" && (
            <>
              <Button variant="outline" size="sm" onClick={handleEdit} className="font-mono text-xs gap-1.5">
                <Pencil className="h-3 w-3" />
                Editar Manual
              </Button>
              <Button size="sm" onClick={handleRetry} className="font-mono text-xs gap-1.5 bg-primary text-primary-foreground">
                <RotateCcw className="h-3 w-3" />
                Reintentar
              </Button>
            </>
          )}
          <Button variant="outline" size="sm" onClick={handleSkip} className="font-mono text-xs gap-1.5 border-warning text-warning hover:bg-warning/10">
            <SkipForward className="h-3 w-3" />
            Omitir Paso
          </Button>
          <Button variant="destructive" size="sm" onClick={handleStop} className="font-mono text-xs gap-1.5">
            <Square className="h-3 w-3" />
            Detener
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
