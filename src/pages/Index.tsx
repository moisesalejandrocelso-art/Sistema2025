import { FlowSidebar } from "@/components/FlowSidebar";
import { FlowStepsList } from "@/components/FlowStepsList";
import { AddStepPanel } from "@/components/AddStepPanel";
import { LogViewer } from "@/components/LogViewer";
import { ElementLibrary } from "@/components/ElementLibrary";
import { ExecutionControls } from "@/components/ExecutionControls";
import { ConfigPanel } from "@/components/ConfigPanel";
import { InitializationPanel } from "@/components/InitializationPanel";
import { ProductsPanel } from "@/components/ProductsPanel";
import { DebugPanel } from "@/components/DebugPanel";
import { StepFailureDialog } from "@/components/StepFailureDialog";
import { useConfigStore } from "@/lib/config-store";
import { useAutomationStore } from "@/lib/automation-store";
import {
  Terminal, Cpu, Settings, Workflow, Bug, Rocket, Package,
} from "lucide-react";

const Index = () => {
  const { activeTab, setActiveTab } = useConfigStore();
  const { flows, activeFlowId } = useAutomationStore();
  const activeFlow = flows.find((f) => f.id === activeFlowId);

  const tabs = [
    { id: "config" as const, label: "Configuración", icon: Settings },
    { id: "flows" as const, label: "Flujos", icon: Workflow },
    { id: "debug" as const, label: "Debug", icon: Bug },
  ];

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-border bg-card shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-primary" />
            <h1 className="font-mono text-sm font-bold text-foreground tracking-tight">
              POS <span className="text-primary">Automation Studio</span>
            </h1>
          </div>

          {/* Tabs */}
          <div className="flex items-center gap-0.5 ml-4 pl-4 border-l border-border">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-mono text-[11px] transition-all ${
                  activeTab === tab.id
                    ? "bg-primary/15 text-primary border border-primary/30"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`}
              >
                <tab.icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {activeTab === "flows" && <ExecutionControls />}
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {activeTab === "config" && (
          <>
            {/* Config main */}
            <div className="flex flex-col flex-1 border-r border-border">
              <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
                <Settings className="h-3.5 w-3.5 text-primary" />
                <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                  Configuración General
                </span>
              </div>
              <ConfigPanel />
            </div>
            {/* Init + Products */}
            <div className="w-80 shrink-0 flex flex-col border-r border-border">
              <InitializationPanel />
            </div>
            <div className="w-72 shrink-0 flex flex-col">
              <ProductsPanel />
            </div>
          </>
        )}

        {activeTab === "flows" && (
          <>
            <div className="w-56 shrink-0">
              <FlowSidebar />
            </div>
            <div className="flex flex-col flex-1 border-r border-border">
              <div className="flex items-center px-3 py-2 border-b border-border">
                <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
                  Pasos del Flujo
                </span>
                {activeFlow && (
                  <span className="ml-auto font-mono text-[10px] text-muted-foreground">
                    {activeFlow.steps.length} pasos · {activeFlow.steps.filter((s) => s.enabled).length} activos
                  </span>
                )}
              </div>
              <FlowStepsList />
              <AddStepPanel />
            </div>
            <div className="w-80 shrink-0 flex flex-col">
              <div className="h-1/2 border-b border-border">
                <ElementLibrary />
              </div>
              <div className="flex-1 min-h-0">
                <LogViewer />
              </div>
            </div>
          </>
        )}

        {activeTab === "debug" && (
          <>
            <div className="flex flex-col flex-1 border-r border-border">
              <DebugPanel />
            </div>
            <div className="w-96 shrink-0 flex flex-col">
              <LogViewer />
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <footer className="flex items-center px-4 py-1.5 border-t border-border bg-card text-[10px] font-mono text-muted-foreground shrink-0">
        <Terminal className="h-3 w-3 mr-1.5" />
        POS Automation Studio v1.0 — Selenium + Appium Backend
      </footer>

      {/* Step failure retry dialog */}
      <StepFailureDialog />
    </div>
  );
};

export default Index;
