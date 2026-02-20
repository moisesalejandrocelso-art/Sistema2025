import { useState } from "react";
import { useAutomationStore } from "@/lib/automation-store";
import { useConfigStore } from "@/lib/config-store";
import { ACTION_LABELS, SELECTOR_LABELS } from "@/lib/automation-types";
import type { ActionType, SelectorType } from "@/lib/automation-types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, X } from "lucide-react";
import { ElementPicker } from "./ElementPicker";

export function AddStepPanel() {
  const { flows, activeFlowId, addStep, elementLibrary } = useAutomationStore();
  const { config } = useConfigStore();
  const [open, setOpen] = useState(false);
  const [actionType, setActionType] = useState<ActionType>("click");
  const [description, setDescription] = useState("");
  const [value, setValue] = useState("");
  const [waitTime, setWaitTime] = useState("1000");
  const [selectorType, setSelectorType] = useState<SelectorType>("name");
  const [selectorValue, setSelectorValue] = useState("");
  const [selectedElementId, setSelectedElementId] = useState<string>("");

  const activeFlow = flows.find((f) => f.id === activeFlowId);

  const handleAdd = () => {
    if (!activeFlow || !description.trim()) return;

    const selectedElement = elementLibrary.find((e) => e.id === selectedElementId);

    // For search_product, always set value to {{products}} placeholder
    const stepValue = actionType === "search_product" ? "{{products}}" : (value || undefined);

    addStep(activeFlow.id, {
      actionType,
      description: description.trim(),
      value: stepValue,
      waitTime: actionType === "wait" ? parseInt(waitTime) : undefined,
      enabled: true,
      elementSelector: selectedElement || (selectorValue ? {
        id: "",
        label: description,
        selectorType,
        selectorValue,
      } : undefined),
    });

    setDescription("");
    setValue("");
    setSelectorValue("");
    setSelectedElementId("");
    setOpen(false);
  };

  const handlePickElement = (pickedSelectorType: string, pickedSelectorValue: string, pickedDescription: string) => {
    setSelectorType(pickedSelectorType as SelectorType);
    setSelectorValue(pickedSelectorValue);
    setSelectedElementId("");
    if (!description) {
      setDescription(pickedDescription);
    }
  };

  if (!activeFlow) return null;

  if (!open) {
    return (
      <div className="p-2 border-t border-border">
        <Button variant="outline" size="sm" onClick={() => setOpen(true)} className="w-full gap-1.5 font-mono text-xs border-dashed border-primary/30 text-primary hover:bg-primary/10">
          <Plus className="h-3.5 w-3.5" /> Agregar Paso
        </Button>
      </div>
    );
  }

  return (
    <div className="p-3 border-t border-border bg-card space-y-3 animate-slide-in">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Nuevo Paso</span>
        <button onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground">
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Acción</label>
          <Select value={actionType} onValueChange={(v) => setActionType(v as ActionType)}>
            <SelectTrigger className="h-8 text-xs font-mono">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(ACTION_LABELS).map(([key, label]) => (
                <SelectItem key={key} value={key} className="text-xs font-mono">{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Descripción</label>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Ej: Clic en botón cobrar" className="h-8 text-xs font-mono" />
        </div>
      </div>

      {(actionType === "type" || actionType === "send_keys") && (
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Valor</label>
          <Input value={value} onChange={(e) => setValue(e.target.value)} placeholder={actionType === "send_keys" ? "Ej: Enter, Tab" : "Texto a escribir"} className="h-8 text-xs font-mono" />
        </div>
      )}

      {actionType === "search_product" && (
        <div className="rounded-md border border-primary/30 bg-primary/5 p-3 space-y-1">
          <p className="text-[10px] font-mono text-primary font-semibold">📦 Búsqueda de Productos</p>
          <p className="text-[10px] font-mono text-muted-foreground">
            Este paso cargará automáticamente los productos del archivo configurado en la inicialización.
          </p>
          <p className="text-[10px] font-mono text-muted-foreground">
            Archivo: <span className="text-foreground">{config.productsFile}</span>
          </p>
          <p className="text-[10px] font-mono text-muted-foreground">
            Productos cargados: <span className="text-primary font-semibold">{config.products.length}</span>
          </p>
        </div>
      )}

      {actionType === "wait" && (
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Tiempo (ms)</label>
          <Input value={waitTime} onChange={(e) => setWaitTime(e.target.value)} type="number" className="h-8 text-xs font-mono" />
        </div>
      )}

      {/* Visual Element Picker from POS */}
      <ElementPicker onSelect={handlePickElement} />

      <div>
        <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Elemento (biblioteca)</label>
        <Select value={selectedElementId} onValueChange={setSelectedElementId}>
          <SelectTrigger className="h-8 text-xs font-mono">
            <SelectValue placeholder="Seleccionar de biblioteca..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none" className="text-xs font-mono">— Ninguno —</SelectItem>
            {elementLibrary.map((el) => (
              <SelectItem key={el.id} value={el.id} className="text-xs font-mono">{el.label} [{el.selectorType}]</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!selectedElementId && (
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Tipo Selector</label>
            <Select value={selectorType} onValueChange={(v) => setSelectorType(v as SelectorType)}>
              <SelectTrigger className="h-8 text-xs font-mono">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(SELECTOR_LABELS).map(([key, label]) => (
                  <SelectItem key={key} value={key} className="text-xs font-mono">{label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="col-span-2">
            <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Valor Selector</label>
            <Input value={selectorValue} onChange={(e) => setSelectorValue(e.target.value)} placeholder="Ej: Borrar pedido" className="h-8 text-xs font-mono" />
          </div>
        </div>
      )}

      <Button size="sm" onClick={handleAdd} disabled={!description.trim()} className="w-full font-mono text-xs bg-primary text-primary-foreground hover:bg-primary/80">
        <Plus className="h-3.5 w-3.5 mr-1" /> Agregar al Flujo
      </Button>
    </div>
  );
}
