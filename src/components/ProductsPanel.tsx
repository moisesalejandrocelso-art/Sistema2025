import { useConfigStore } from "@/lib/config-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2, Package, Upload, FileDown, Loader2 } from "lucide-react";
import { useState } from "react";
import { loadProductsFromFile } from "@/lib/api-client";
import { toast } from "sonner";

export function ProductsPanel() {
  const { config, addProduct, removeProduct, setProducts } = useConfigStore();
  const [newCode, setNewCode] = useState("");
  const [newQty, setNewQty] = useState("1");
  const [loading, setLoading] = useState(false);

  const handleAdd = () => {
    if (newCode.trim()) {
      addProduct(newCode.trim(), parseInt(newQty) || 1);
      setNewCode("");
      setNewQty("1");
    }
  };

  const handleLoadFromFile = async () => {
    if (!config.productsFile.trim()) {
      toast.error("Configura la ruta del archivo de productos primero");
      return;
    }
    setLoading(true);
    try {
      const res = await loadProductsFromFile(config.productsFile);
      if (res.status === "success" && res.products) {
        setProducts(res.products);
        toast.success(`${res.count} productos cargados desde archivo`);
      } else {
        toast.error(res.error || "Error cargando productos");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error de conexión";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePasteImport = () => {
    const text = prompt("Pega el contenido del archivo de productos (código,cantidad por línea):");
    if (!text) return;
    const lines = text.split("\n").filter((l) => l.trim());
    const parsed = lines.map((line) => {
      const parts = line.split(",");
      return {
        code: parts[0]?.trim() || "",
        quantity: parseInt(parts[1]?.trim() || "1") || 1,
      };
    }).filter((p) => p.code);
    if (parsed.length) setProducts(parsed);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-border">
        <div className="flex items-center gap-2">
          <Package className="h-3.5 w-3.5 text-primary" />
          <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">
            Productos ({config.products.length})
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLoadFromFile}
            disabled={loading}
            className="h-6 px-2 text-muted-foreground hover:text-primary gap-1"
            title="Cargar desde archivo configurado"
          >
            {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileDown className="h-3 w-3" />}
            <span className="text-[10px]">Archivo</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handlePasteImport}
            className="h-6 px-2 text-muted-foreground hover:text-primary gap-1"
          >
            <Upload className="h-3 w-3" />
            <span className="text-[10px]">Pegar</span>
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-2 space-y-1">
        {config.products.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground font-mono text-[11px] gap-2 p-4">
            <Package className="h-6 w-6 opacity-40" />
            <span>Sin productos cargados</span>
            <span className="text-[10px] text-center">Usa "Archivo" para cargar desde<br/>{config.productsFile.split("\\").pop() || "archivo"}</span>
          </div>
        )}
        {config.products.map((p, i) => (
          <div key={i} className="group flex items-center gap-2 px-2 py-1.5 rounded border border-border bg-card hover:border-primary/30 transition">
            <span className="font-mono text-[10px] text-muted-foreground w-4 text-right">{i + 1}</span>
            <span className="font-mono text-xs text-foreground flex-1">{p.code}</span>
            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-secondary text-primary">×{p.quantity}</span>
            <button onClick={() => removeProduct(i)} className="opacity-0 group-hover:opacity-100 text-destructive transition">
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>

      <div className="p-2 border-t border-border">
        <div className="flex gap-1">
          <Input
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            placeholder="Código producto"
            className="h-7 text-xs font-mono flex-1"
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <Input
            value={newQty}
            onChange={(e) => setNewQty(e.target.value)}
            type="number"
            min={1}
            className="h-7 text-xs font-mono w-14"
          />
          <Button size="sm" onClick={handleAdd} disabled={!newCode.trim()} className="h-7 px-2">
            <Plus className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}
