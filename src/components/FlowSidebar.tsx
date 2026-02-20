import { useAutomationStore } from "@/lib/automation-store";
import { Plus, Workflow, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Input } from "@/components/ui/input";

export function FlowSidebar() {
  const { flows, activeFlowId, setActiveFlow, addFlow, deleteFlow } = useAutomationStore();
  const [isAdding, setIsAdding] = useState(false);
  const [newName, setNewName] = useState("");

  const handleAdd = () => {
    if (newName.trim()) {
      addFlow(newName.trim(), "");
      setNewName("");
      setIsAdding(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-sidebar border-r border-sidebar-border">
      <div className="flex items-center justify-between px-3 py-3 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <Workflow className="h-4 w-4 text-sidebar-primary" />
          <span className="font-mono text-xs font-semibold text-sidebar-foreground uppercase tracking-wider">Flujos</span>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setIsAdding(!isAdding)} className="h-6 w-6 p-0 text-sidebar-foreground hover:text-sidebar-primary">
          <Plus className="h-3.5 w-3.5" />
        </Button>
      </div>

      {isAdding && (
        <div className="p-2 border-b border-sidebar-border">
          <Input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nombre del flujo..."
            className="h-7 text-xs font-mono bg-sidebar-accent border-sidebar-border"
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            autoFocus
          />
        </div>
      )}

      <div className="flex-1 overflow-y-auto scrollbar-thin p-1 space-y-0.5">
        {flows.map((flow) => (
          <button
            key={flow.id}
            onClick={() => setActiveFlow(flow.id)}
            className={`group w-full flex items-center justify-between px-3 py-2 rounded-md text-left transition-all ${
              activeFlowId === flow.id
                ? "bg-sidebar-accent text-sidebar-accent-foreground border border-sidebar-primary/30"
                : "text-sidebar-foreground hover:bg-sidebar-accent/50"
            }`}
          >
            <div className="min-w-0">
              <div className="text-xs font-medium truncate">{flow.name}</div>
              <div className="text-[10px] font-mono text-muted-foreground">{flow.steps.length} pasos</div>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); deleteFlow(flow.id); }}
              className="opacity-0 group-hover:opacity-100 text-destructive hover:text-destructive/80 transition shrink-0"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </button>
        ))}
      </div>
    </div>
  );
}
