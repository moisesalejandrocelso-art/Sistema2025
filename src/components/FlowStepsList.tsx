import { useAutomationStore } from "@/lib/automation-store";
import { useConfigStore } from "@/lib/config-store";
import { ACTION_LABELS, SELECTOR_LABELS } from "@/lib/automation-types";
import {
  MousePointer2, Type, Keyboard, Clock, Trash2, GripVertical, Pencil, Check, X,
  MousePointerClick, ListChecks, ArrowDownUp, Eraser, CircleDot, CheckCircle2, Search, Play,
} from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useState } from "react";
import type { ActionType, FlowStep, SelectorType } from "@/lib/automation-types";
import { ElementPicker } from "./ElementPicker";

const actionIcons: Record<ActionType, React.ReactNode> = {
  click: <MousePointer2 className="h-3.5 w-3.5" />,
  double_click: <MousePointerClick className="h-3.5 w-3.5" />,
  type: <Type className="h-3.5 w-3.5" />,
  send_keys: <Keyboard className="h-3.5 w-3.5" />,
  wait: <Clock className="h-3.5 w-3.5" />,
  clear: <Eraser className="h-3.5 w-3.5" />,
  select_combo: <ListChecks className="h-3.5 w-3.5" />,
  select_radio: <CircleDot className="h-3.5 w-3.5" />,
  scroll: <ArrowDownUp className="h-3.5 w-3.5" />,
  assert: <CheckCircle2 className="h-3.5 w-3.5" />,
  search_product: <Search className="h-3.5 w-3.5" />,
};

export function FlowStepsList() {
  const { flows, activeFlowId, deleteStep, updateStep, currentStepIndex, executionStatus, startFromStepIndex, setStartFromStepIndex } = useAutomationStore();
  const activeFlow = flows.find((f) => f.id === activeFlowId);
  const [editingStepId, setEditingStepId] = useState<string | null>(null);

  if (!activeFlow) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground font-mono text-sm p-8">
        Selecciona o crea un flujo para comenzar
      </div>
    );
  }

  if (activeFlow.steps.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground font-mono text-sm p-8">
        No hay pasos. Agrega uno con el botón +
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
      {activeFlow.steps.map((step, index) => (
        editingStepId === step.id ? (
          <StepEditor
            key={step.id}
            step={step}
            onSave={(updates) => {
              updateStep(activeFlow.id, step.id, updates);
              setEditingStepId(null);
            }}
            onCancel={() => setEditingStepId(null)}
          />
        ) : (
          <StepItem
            key={step.id}
            step={step}
            index={index}
            isActive={currentStepIndex === step.order && executionStatus === "running"}
            isStartFrom={startFromStepIndex === index}
            onToggle={() => updateStep(activeFlow.id, step.id, { enabled: !step.enabled })}
            onDelete={() => deleteStep(activeFlow.id, step.id)}
            onEdit={() => setEditingStepId(step.id)}
            onSetStartFrom={() => setStartFromStepIndex(index)}
          />
        )
      ))}
    </div>
  );
}

function StepItem({
  step, index, isActive, isStartFrom, onToggle, onDelete, onEdit, onSetStartFrom,
}: {
  step: FlowStep; index: number; isActive: boolean; isStartFrom: boolean;
  onToggle: () => void; onDelete: () => void; onEdit: () => void; onSetStartFrom: () => void;
}) {
  const { config } = useConfigStore();

  return (
    <div
      onDoubleClick={onEdit}
      className={`group flex items-center gap-2 rounded-md border px-3 py-2 transition-all cursor-pointer ${
        isActive
          ? "border-primary bg-primary/10 glow-primary"
          : isStartFrom
          ? "border-success bg-success/10"
          : step.enabled
          ? "border-border bg-card hover:border-muted-foreground/30"
          : "border-border/50 bg-muted/30 opacity-50"
      }`}
    >
      <GripVertical className="h-3.5 w-3.5 text-muted-foreground cursor-grab shrink-0" />
      <span className="font-mono text-[10px] text-muted-foreground w-5 text-right shrink-0">{index + 1}</span>
      <span className="text-primary shrink-0">{actionIcons[step.actionType]}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">
            {ACTION_LABELS[step.actionType]}
          </span>
          <span className="text-xs text-foreground truncate">{step.description}</span>
        </div>
        {(step.value || step.elementSelector) && (
          <div className="flex items-center gap-2 mt-1">
            {step.elementSelector && (
              <span className="font-mono text-[10px] text-muted-foreground">
                [{step.elementSelector.selectorType}] {step.elementSelector.selectorValue}
              </span>
            )}
            {step.value && (
              <span className="font-mono text-[10px] text-primary/70">
                {step.actionType === "search_product" && step.value === "{{products}}"
                  ? `→ 📦 ${config.products.length} productos cargados`
                  : step.value === "{{payment_amount}}"
                  ? `→ 💰 $${config.paymentAmount.toLocaleString()}`
                  : `→ "${step.value}"`}
              </span>
            )}
          </div>
        )}
      </div>
      <Tooltip>
        <TooltipTrigger asChild>
          <button onClick={onSetStartFrom} className={`shrink-0 transition ${isStartFrom ? "text-success" : "opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-success"}`} title="Ejecutar desde aquí">
            <Play className="h-3 w-3" />
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs font-mono">Ejecutar desde aquí</TooltipContent>
      </Tooltip>
      <button onClick={onEdit} className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-primary transition shrink-0" title="Editar paso">
        <Pencil className="h-3 w-3" />
      </button>
      <Switch checked={step.enabled} onCheckedChange={onToggle} className="shrink-0 scale-75" />
      <button onClick={onDelete} className="opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive/80 transition shrink-0">
        <Trash2 className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function StepEditor({
  step, onSave, onCancel,
}: {
  step: FlowStep;
  onSave: (updates: Partial<FlowStep>) => void; onCancel: () => void;
}) {
  const { elementLibrary } = useAutomationStore();
  const [actionType, setActionType] = useState<ActionType>(step.actionType);
  const [description, setDescription] = useState(step.description);
  const [value, setValue] = useState(step.value || "");
  const [selectorType, setSelectorType] = useState<SelectorType>(step.elementSelector?.selectorType || "name");
  const [selectorValue, setSelectorValue] = useState(step.elementSelector?.selectorValue || "");
  const [waitTime, setWaitTime] = useState(String(step.waitTime || 1000));
  const [selectedElementId, setSelectedElementId] = useState<string>(step.elementSelector?.id || "");

  const handleSave = () => {
    const stepValue = actionType === "search_product" ? "{{products}}" : (value || undefined);
    const selectedElement = elementLibrary.find((e) => e.id === selectedElementId);
    
    onSave({
      actionType,
      description,
      value: stepValue,
      waitTime: actionType === "wait" ? parseInt(waitTime) : undefined,
      elementSelector: selectedElement ? selectedElement : (selectorValue ? {
        id: step.elementSelector?.id || "",
        label: description,
        selectorType,
        selectorValue,
      } : undefined),
    });
  };

  const handlePickElement = (pickedSelectorType: string, pickedSelectorValue: string, pickedDescription: string) => {
    setSelectorType(pickedSelectorType as SelectorType);
    setSelectorValue(pickedSelectorValue);
    setSelectedElementId("");
    if (!description) {
      setDescription(pickedDescription);
    }
  };

  return (
    <div className="rounded-md border-2 border-primary bg-card p-3 space-y-2 animate-slide-in">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] text-primary uppercase tracking-wider">Editando paso</span>
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={handleSave} className="h-6 px-2 text-success hover:text-success">
            <Check className="h-3 w-3" />
          </Button>
          <Button size="sm" variant="ghost" onClick={onCancel} className="h-6 px-2 text-destructive hover:text-destructive">
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Acción</label>
          <Select value={actionType} onValueChange={(v) => setActionType(v as ActionType)}>
            <SelectTrigger className="h-7 text-xs font-mono">
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
          <Input value={description} onChange={(e) => setDescription(e.target.value)} className="h-7 text-xs font-mono" />
        </div>
      </div>
      {(actionType === "type" || actionType === "send_keys") && (
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Valor</label>
          <Input value={value} onChange={(e) => setValue(e.target.value)} className="h-7 text-xs font-mono" />
        </div>
      )}
      {actionType === "wait" && (
        <div>
          <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Tiempo (ms)</label>
          <Input value={waitTime} onChange={(e) => setWaitTime(e.target.value)} type="number" className="h-7 text-xs font-mono" />
        </div>
      )}
      
      {/* Visual Element Picker from POS */}
      <ElementPicker onSelect={handlePickElement} />

      {/* Element from Library */}
      <div>
        <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Elemento (biblioteca)</label>
        <Select value={selectedElementId} onValueChange={setSelectedElementId}>
          <SelectTrigger className="h-7 text-xs font-mono">
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

      {/* Manual Element Entry */}
      {!selectedElementId && (
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[10px] font-mono text-muted-foreground mb-1 block">Tipo Selector</label>
            <Select value={selectorType} onValueChange={(v) => setSelectorType(v as SelectorType)}>
              <SelectTrigger className="h-7 text-xs font-mono">
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
            <Input value={selectorValue} onChange={(e) => setSelectorValue(e.target.value)} className="h-7 text-xs font-mono" />
          </div>
        </div>
      )}
    </div>
  );
}
