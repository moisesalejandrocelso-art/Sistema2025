import { create } from "zustand";

export interface ProductEntry {
  code: string;
  quantity: number;
}

export interface AppConfig {
  backendUrl: string;
  appPath: string;
  appiumUrl: string;
  productsFile: string;
  products: ProductEntry[];
  iterations: number;
  productsPerIteration: number;
  comboBoxName: string;
  comboBoxOption: string;
  radioButtonName: string;
  paymentAmount: number;
  stepDelay: number;
  retryAttempts: number;
  retryDelay: number;
  enableDebug: boolean;
}

export interface InitStep {
  id: string;
  name: string;
  status: "pending" | "running" | "success" | "error" | "skipped";
  message?: string;
}

interface ConfigState {
  config: AppConfig;
  initSteps: InitStep[];
  isInitialized: boolean;
  activeTab: "config" | "flows" | "debug";

  updateConfig: (updates: Partial<AppConfig>) => void;
  setProducts: (products: ProductEntry[]) => void;
  addProduct: (code: string, quantity: number) => void;
  removeProduct: (index: number) => void;
  setInitSteps: (steps: InitStep[]) => void;
  updateInitStep: (id: string, updates: Partial<InitStep>) => void;
  setIsInitialized: (v: boolean) => void;
  setActiveTab: (tab: "config" | "flows" | "debug") => void;
}

const defaultConfig: AppConfig = {
  backendUrl: "http://localhost:8000",
  appPath: "C:\\colombia\\110625_1_R_Cobro_Facturacion\\SimiPOS_PV_Desktop.UI.exe",
  appiumUrl: "http://127.0.0.1:4723",
  productsFile: "c:\\Colombia\\Automatizacion PV\\productos_con_cantidades.txt",
  products: [],
  iterations: 4,
  productsPerIteration: 10,
  comboBoxName: "Venta asignada a",
  comboBoxOption: "usr008 - Armando Gonzalez",
  radioButtonName: "Consumidor final",
  paymentAmount: 500000,
  stepDelay: 1000,
  retryAttempts: 3,
  retryDelay: 2000,
  enableDebug: false,
};

const defaultInitSteps: InitStep[] = [
  { id: "check_appium", name: "Verificar servidor Appium", status: "pending" },
  { id: "open_app", name: "Abrir aplicación POS", status: "pending" },
  { id: "connect_appium", name: "Conectar sesión Appium", status: "pending" },
  { id: "clear_order", name: "Limpiar pedido anterior", status: "pending" },
  { id: "load_products", name: "Cargar lista de productos", status: "pending" },
];

export const useConfigStore = create<ConfigState>((set) => ({
  config: defaultConfig,
  initSteps: defaultInitSteps,
  isInitialized: false,
  activeTab: "config",

  updateConfig: (updates) =>
    set((s) => ({ config: { ...s.config, ...updates } })),

  setProducts: (products) =>
    set((s) => ({ config: { ...s.config, products } })),

  addProduct: (code, quantity) =>
    set((s) => ({ config: { ...s.config, products: [...s.config.products, { code, quantity }] } })),

  removeProduct: (index) =>
    set((s) => ({
      config: { ...s.config, products: s.config.products.filter((_, i) => i !== index) },
    })),

  setInitSteps: (steps) => set({ initSteps: steps }),

  updateInitStep: (id, updates) =>
    set((s) => ({
      initSteps: s.initSteps.map((st) => (st.id === id ? { ...st, ...updates } : st)),
    })),

  setIsInitialized: (v) => set({ isInitialized: v }),
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
