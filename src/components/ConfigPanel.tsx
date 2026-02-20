import { useConfigStore } from "@/lib/config-store";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  FolderOpen, Globe, FileText, Hash, DollarSign, Bug, ListChecks, CircleDot, Repeat, Server, Timer, RotateCcw,
} from "lucide-react";

export function ConfigPanel() {
  const { config, updateConfig } = useConfigStore();

  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-5">
      <Section icon={<Server className="h-4 w-4 text-primary" />} title="Backend">
        <Field label="URL del backend (FastAPI)">
          <Input
            value={config.backendUrl}
            onChange={(e) => updateConfig({ backendUrl: e.target.value })}
            className="h-8 text-xs font-mono"
            placeholder="http://localhost:8000"
          />
        </Field>
        <p className="text-[10px] font-mono text-muted-foreground/60">
          Usa un DevTunnel o ngrok para acceso remoto. Ej: https://xxx.devtunnels.ms
        </p>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<FolderOpen className="h-4 w-4 text-primary" />} title="Aplicación POS">
        <Field label="Ruta del ejecutable (.exe)">
          <Input
            value={config.appPath}
            onChange={(e) => updateConfig({ appPath: e.target.value })}
            className="h-8 text-xs font-mono"
            placeholder="C:\ruta\a\SimiPOS.exe"
          />
        </Field>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<Globe className="h-4 w-4 text-primary" />} title="Servidor Appium">
        <Field label="URL del servidor">
          <Input
            value={config.appiumUrl}
            onChange={(e) => updateConfig({ appiumUrl: e.target.value })}
            className="h-8 text-xs font-mono"
            placeholder="http://127.0.0.1:4723"
          />
        </Field>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<FileText className="h-4 w-4 text-primary" />} title="Archivo de Productos">
        <Field label="Ruta del archivo de productos (.txt)">
          <Input
            value={config.productsFile}
            onChange={(e) => updateConfig({ productsFile: e.target.value })}
            className="h-8 text-xs font-mono"
            placeholder="C:\ruta\productos.txt"
          />
        </Field>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<Repeat className="h-4 w-4 text-primary" />} title="Ejecución">
        <div className="grid grid-cols-3 gap-3">
          <Field label="Iteraciones">
            <Input
              type="number"
              min={1}
              value={config.iterations}
              onChange={(e) => updateConfig({ iterations: parseInt(e.target.value) || 1 })}
              className="h-8 text-xs font-mono"
            />
          </Field>
          <Field label="Productos por iteración">
            <Input
              type="number"
              min={1}
              value={config.productsPerIteration}
              onChange={(e) => updateConfig({ productsPerIteration: parseInt(e.target.value) || 1 })}
              className="h-8 text-xs font-mono"
            />
          </Field>
          <Field label="Monto de pago">
            <div className="relative">
              <DollarSign className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
              <Input
                type="number"
                value={config.paymentAmount}
                onChange={(e) => updateConfig({ paymentAmount: parseFloat(e.target.value) || 0 })}
                className="h-8 text-xs font-mono pl-7"
              />
            </div>
          </Field>
        </div>
        <p className="text-[10px] font-mono text-muted-foreground/60">
          Se seleccionarán aleatoriamente {config.productsPerIteration} productos del archivo por cada iteración.
        </p>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<Timer className="h-4 w-4 text-primary" />} title="Espera y Reintentos">
        <div className="grid grid-cols-3 gap-3">
          <Field label="Espera entre pasos (ms)">
            <Input
              type="number"
              min={0}
              step={500}
              value={config.stepDelay}
              onChange={(e) => updateConfig({ stepDelay: parseInt(e.target.value) || 0 })}
              className="h-8 text-xs font-mono"
            />
          </Field>
          <Field label="Reintentos si no encuentra">
            <Input
              type="number"
              min={1}
              max={10}
              value={config.retryAttempts}
              onChange={(e) => updateConfig({ retryAttempts: parseInt(e.target.value) || 1 })}
              className="h-8 text-xs font-mono"
            />
          </Field>
          <Field label="Espera entre reintentos (ms)">
            <Input
              type="number"
              min={500}
              step={500}
              value={config.retryDelay}
              onChange={(e) => updateConfig({ retryDelay: parseInt(e.target.value) || 1000 })}
              className="h-8 text-xs font-mono"
            />
          </Field>
        </div>
        <p className="text-[10px] font-mono text-muted-foreground/60">
          Si un elemento no se encuentra, reintentará {config.retryAttempts} veces esperando {config.retryDelay}ms entre cada intento.
        </p>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<ListChecks className="h-4 w-4 text-primary" />} title="Valores por Defecto">
        <div className="grid grid-cols-2 gap-3">
          <Field label="ComboBox — Nombre">
            <Input
              value={config.comboBoxName}
              onChange={(e) => updateConfig({ comboBoxName: e.target.value })}
              className="h-8 text-xs font-mono"
            />
          </Field>
          <Field label="ComboBox — Opción">
            <Input
              value={config.comboBoxOption}
              onChange={(e) => updateConfig({ comboBoxOption: e.target.value })}
              className="h-8 text-xs font-mono"
            />
          </Field>
        </div>
        <Field label="RadioButton — Nombre">
          <Input
            value={config.radioButtonName}
            onChange={(e) => updateConfig({ radioButtonName: e.target.value })}
            className="h-8 text-xs font-mono"
          />
        </Field>
      </Section>

      <Separator className="bg-border" />

      <Section icon={<Bug className="h-4 w-4 text-warning" />} title="Debug">
        <div className="flex items-center justify-between">
          <Label className="text-xs font-mono text-muted-foreground">Activar modo debug</Label>
          <Switch
            checked={config.enableDebug}
            onCheckedChange={(v) => updateConfig({ enableDebug: v })}
          />
        </div>
        <p className="text-[10px] font-mono text-muted-foreground/60 mt-1">
          Captura elementos de pantalla, análisis de ventanas y logs detallados durante la ejecución.
        </p>
      </Section>
    </div>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="font-mono text-xs font-semibold text-foreground uppercase tracking-wider">{title}</h3>
      </div>
      <div className="space-y-2 pl-6">{children}</div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-[10px] font-mono text-muted-foreground mb-1 block">{label}</label>
      {children}
    </div>
  );
}
