import { useState } from "react";
import { useAutomationStore } from "@/lib/automation-store";
import { SELECTOR_LABELS } from "@/lib/automation-types";
import type { SelectorType } from "@/lib/automation-types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Trash2, Database, X } from "lucide-react";

export function ElementLibrary() {
  const { elementLibrary, addElement, deleteElement } = useAutomationStore();
  const [isAdding, setIsAdding] = useState(false);
  const [label, setLabel] = useState("");
  const [selectorType, setSelectorType] = useState<SelectorType>("name");
  const [selectorValue, setSelectorValue] = useState("");
  const [description, setDescription] = useState("");

  const handleAdd = () => {
    if (!label.trim() || !selectorValue.trim()) return;
    addElement({ label: label.trim(), selectorType, selectorValue: selectorValue.trim(), description: description.trim() || undefined });
    setLabel("");
    setSelectorValue("");
    setDescription("");
    setIsAdding(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          <Database className="h-3.5 w-3.5 text-primary" />
          <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Elementos</span>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setIsAdding(!isAdding)} className="h-6 w-6 p-0 text-muted-foreground hover:text-primary">
          {isAdding ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
        </Button>
      </div>

      {isAdding && (
        <div className="p-3 border-b border-border space-y-2 animate-slide-in bg-card">
          <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Nombre del elemento" className="h-7 text-xs font-mono" autoFocus />
          <div className="grid grid-cols-3 gap-1">
            <Select value={selectorType} onValueChange={(v) => setSelectorType(v as SelectorType)}>
              <SelectTrigger className="h-7 text-[10px] font-mono"><SelectValue /></SelectTrigger>
              <SelectContent>
                {Object.entries(SELECTOR_LABELS).map(([k, v]) => (
                  <SelectItem key={k} value={k} className="text-xs font-mono">{v}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input value={selectorValue} onChange={(e) => setSelectorValue(e.target.value)} placeholder="Valor" className="h-7 text-[10px] font-mono col-span-2" />
          </div>
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Descripción (opcional)" className="h-7 text-[10px] font-mono" />
          <Button size="sm" onClick={handleAdd} disabled={!label.trim() || !selectorValue.trim()} className="w-full h-7 text-[10px] font-mono">
            <Plus className="h-3 w-3 mr-1" /> Guardar
          </Button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
        {elementLibrary.map((el) => (
          <div key={el.id} className="group flex items-center gap-2 px-2 py-1.5 rounded border border-border bg-card hover:border-primary/30 transition">
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium truncate">{el.label}</div>
              <div className="font-mono text-[10px] text-muted-foreground truncate">
                <span className="text-primary/60">[{el.selectorType}]</span> {el.selectorValue}
              </div>
            </div>
            <button onClick={() => deleteElement(el.id)} className="opacity-0 group-hover:opacity-100 text-destructive transition shrink-0">
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
